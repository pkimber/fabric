# -*- encoding: utf-8 -*-
import glob
import os
import shutil
import tempfile

from datetime import datetime
from walkdir import (
    file_paths,
    filtered_walk,
)

from fabric.api import (
    abort,
    local,
    prompt,
)
from fabric.colors import (
    cyan,
    green,
    yellow,
)
from fabric.context_managers import shell_env

from lib.path import Path
from lib.postgres import (
    drop_local_database,
    local_database_create,
    local_database_exists,
    local_load_file,
    local_reassign_owner,
    local_user_create,
    local_user_exists,
)


class Duplicity(object):

    def __init__(self, site_info, backup_or_files):
        self.backup = False
        self.files = False
        if backup_or_files == 'backup':
            self.backup = True
            if site_info.is_postgres:
                file_type = 'postgres'
            elif site_info.is_mysql:
                file_type = 'mysql'
            else:
                abort(
                    "Sorry, this site is not using a 'postgres' database. "
                    "I don't know how to restore it (yet)."
                )
        elif backup_or_files == 'files':
            self.files = True
            file_type = 'files'
        else:
            abort(
                "Only 'backup' and 'files' are valid operations for duplicity "
                "commands (not '{}')".format(backup_or_files)
            )
        self.backup_or_files = backup_or_files
        self.path = Path(site_info.domain, file_type)
        self.site_info = site_info

    def _display_backup_not_restored(self, restore_to, sql_file):
        print
        count = 0
        files = file_paths(filtered_walk(restore_to))
        for item in files:
            if sql_file == item:
                pass
            else:
                count = count + 1
                print('{}. {}'.format(count, item))
        if count:
            print(yellow(
                "The {} files listed above were not restored "
                "(just so you know).".format(count)
            ))
            print

    def _display_files_not_restored(self, restore_to):
        print
        count = 0
        files = file_paths(filtered_walk(restore_to))
        for item in files:
            count = count + 1
            print('{}. {}'.format(count, item))
        if count:
            print(yellow(
                "The {} files listed above were not restored "
                "(just so you know).".format(count)
            ))
            print

    def _find_sql(self, restore_to):
        result = None
        found = None
        match = glob.glob('{}/*.sql'.format(restore_to))
        for item in match:
            print('found: {}'.format(os.path.basename(item)))
            file_name, extension = os.path.splitext(os.path.basename(item))
            file_date_time = datetime.strptime(file_name, '%Y%m%d_%H%M')
            if not found or file_date_time > found:
                found = file_date_time
                result = item
        if result:
            print('restoring: {}'.format(os.path.basename(result)))
        else:
            abort("Cannot find any SQL files to restore.")
        return result

    def _heading(self, command):
        print(yellow("{}: {} for {}").format(
            command,
            self.backup_or_files,
            self.site_info.domain,
        ))

    def _repo(self):
        return '{}{}/{}'.format(
            self.site_info.rsync_ssh,
            self.site_info.domain,
            self.backup_or_files,
        )

    def _restore(self, restore_to):
        env = {
            'PASSPHRASE': self.site_info.rsync_gpg_password,
        }
        with shell_env(**env):
            local('duplicity restore {} {}'.format(
                self._repo(),
                restore_to,
            ))

    def _restore_database(self, restore_to):
        sql_file = self._find_sql(restore_to)
        print(green("restore to test database: {}".format(sql_file)))
        if self.site_info.is_mysql:
            self._restore_database_mysql(sql_file)
        elif self.site_info.is_postgres:
            self._restore_database_postgres(restore_to, sql_file)
        else:
            abort("Nothing to do... (this is a problem)")
        return sql_file

    def _restore_database_mysql(self, sql_file):
        local_project_folder = self.path.local_project_folder(
            self.site_info.site_name
        )
        to_sql_file = os.path.join(local_project_folder, "mysqldump.sql")
        from_to = []
        from_to.append((sql_file, to_sql_file))
        self._remove_files_folders(from_to)
        # move the files/folders to the project folder
        for from_file, to_file in from_to:
            shutil.move(from_file, to_file)

    def _restore_database_postgres(self, restore_to, sql_file):
        database_name = self.path.test_database_name()
        if local_database_exists(database_name):
            drop_local_database(database_name)
        local_database_create(database_name)
        if not local_user_exists(self.site_info):
            local_user_create(self.site_info)
        local_load_file(database_name, sql_file)
        local_reassign_owner(
            database_name,
            self.site_info.db_name,
            self.path.user_name()
        )
        print(green("psql {}").format(database_name))

    def _remove_file_or_folder(self, file_name):
        if os.path.exists(file_name):
            if os.path.isdir(file_name):
                shutil.rmtree(file_name)
            elif os.path.isfile(file_name):
                os.remove(file_name)
            else:
                abort("Is not a file or folder: {}".format(file_name))

    def _remove_files_folders(self, from_to):
        count = 0
        print
        for ignore, to_file in from_to:
            if os.path.exists(to_file):
                count = count + 1
                print('{}. {}'.format(count, to_file))
        if count:
            confirm = ''
            while confirm not in ('Y', 'N'):
                confirm = prompt(
                    "Are you happy to remove these {} files/folders?".format(
                        count
                    ))
                confirm = confirm.strip().upper()
            if confirm == 'Y':
                for ignore, to_file in from_to:
                    self._remove_file_or_folder(to_file)
            else:
                abort("Cannot restore unless existing files are removed.")
        else:
            print("No files or folders to remove from the project folder.")

    def _get_from_to(self, temp_folder, project_folder):
        result = []
        match = glob.glob('{}/*'.format(temp_folder))
        for item in match:
            folder = os.path.join(
                project_folder,
                os.path.basename(item),
            )
            result.append((item, folder))
        result.sort() # required for the test
        return result

    def _restore_files(self, restore_to):
        if self.site_info.is_php:
            self._restore_files_php_site(restore_to)
        else:
            self._restore_files_django_site(restore_to)

    def _restore_files_django_site(self, restore_to):
        from_to = self._get_from_to(
            os.path.join(restore_to, 'public'),
            self.path.local_project_folder_media(self.site_info.package),
        )
        from_to = from_to + self._get_from_to(
            os.path.join(restore_to, 'private'),
            self.path.local_project_folder_media_private(self.site_info.package),
        )
        self._remove_files_folders(from_to)
        # move the files/folders to the project folder
        for from_file, to_file in from_to:
            shutil.move(from_file, to_file)

    def _restore_files_php_site(self, restore_to):
        from_to = self._get_from_to(
            restore_to,
            self.path.local_project_folder(self.site_info.site_name),
        )
        self._remove_files_folders(from_to)
        # move the files/folders to the project folder
        for from_file, to_file in from_to:
            shutil.move(from_file, to_file)

    def list_current(self):
        self._heading('list_current')
        local('duplicity collection-status {}'.format(self._repo()))

    def restore(self):
        self._heading('restore')
        try:
            restore_to = tempfile.mkdtemp()
            self._restore(restore_to)
            if self.backup:
                sql_file = self._restore_database(restore_to)
                self._display_backup_not_restored(restore_to, sql_file)
            elif self.files:
                self._restore_files(restore_to)
                self._display_files_not_restored(restore_to)
            else:
                abort("Nothing to do... (this is a problem)")
        finally:
            if os.path.exists(restore_to):
                #shutil.rmtree(restore_to)
                pass
        self._heading('Complete')
