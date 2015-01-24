# -*- encoding: utf-8 -*-
import glob
import os
import shutil
import tempfile

from datetime import datetime

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

from lib.backup.path import Path
from lib.postgres import (
    local_database_exists,
    local_postgres_user_exists,
)


class Duplicity(object):

    def __init__(self, site_info, backup_or_files):
        self.backup = False
        self.files = False
        if backup_or_files == 'backup':
            self.backup = True
            if site_info.is_postgres():
                file_type = 'postgres'
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
        self.path = Path(site_info.site_name, file_type)
        self.site_info = site_info

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
            self.site_info.site_name,
        ))

    def _repo(self):
        return '{}{}/{}'.format(
            self.site_info.rsync_ssh,
            self.site_info.site_name,
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
        if local_database_exists(self.path.test_database_name()):
            local('psql -X -U postgres -c "DROP DATABASE {0}"'.format(self.path.test_database_name()))
        local('psql -X -U postgres -c "CREATE DATABASE {0} TEMPLATE=template0 ENCODING=\'utf-8\';"'.format(self.path.test_database_name()))
        if not local_postgres_user_exists(self.site_info.site_name):
            local('psql -X -U postgres -c "CREATE ROLE {0} WITH PASSWORD \'{1}\' NOSUPERUSER CREATEDB NOCREATEROLE LOGIN;"'.format(env.site_info.site_name, env.site_info.site_name))
        local("psql -X --set ON_ERROR_STOP=on -U postgres -d {0} --file {1}".format(
            self.path.test_database_name(), sql_file), capture=True
        )
        local('psql -X -U postgres -d {} -c "REASSIGN OWNED BY {} TO {}"'.format(
            self.path.test_database_name(), self.site_info.site_name, self.path.user_name()
        ))
        print(green("psql {}").format(self.path.test_database_name()))

    def _restore_files(self, restore_to):
        print restore_to
        print self.path.local_project_folder_media(self.site_info.site_name)
        temp_public = os.path.join(restore_to, 'public')
        match = glob.glob('{}/*'.format(temp_public))
        print match
        to_remove = []
        for item in match:
            project_folder = os.path.join(
                self.path.local_project_folder_media(self.site_info.site_name),
                os.path.basename(item),
            )
            print project_folder
            if os.path.exists(project_folder):
                to_remove.append(project_folder)
        if to_remove:
            print
            for count, item in enumerate(to_remove):
                print('{}. {}'.format(count + 1, item))
            confirm = ''
            while confirm not in ('Y', 'N'):
                confirm = prompt(
                    "Are you happy to remove these {} files/folders?".format(
                        len(to_remove)
                    ))
                confirm = confirm.strip().upper()
            if confirm == 'Y':
                for item in to_remove:
                    if os.path.isdir(item):
                        shutil.rmtree(item)
                    elif os.path.isfile(item):
                        os.remove(item)
                    else:
                        abort("Is not a file or folder: {}".format(item))
            else:
                abort("Cannot restore unless existing files are removed.")
        # move the files/folders to the project folder
        for item in match:
            print(item)
            project_folder = os.path.join(
                self.path.local_project_folder_media(self.site_info.site_name),
                os.path.basename(item),
            )
            print('move: {}'.format(item))
            print('  to: {}'.format(project_folder))
            shutil.move(item, project_folder)



    def list_current(self):
        self._heading('list_current')
        local('duplicity collection-status {}'.format(self._repo()))

    def restore(self):
        self._heading('restore')
        try:
            # Uncomment this when it is all working
            # restore_to = tempfile.mkdtemp()
            # self._restore(restore_to)
            if self.backup:
                self._restore_database(restore_to)
            if self.files:
                #self._restore_files(restore_to)
                self._restore_files('/tmp/tmpSA8G7z')
        finally:
            # Uncomment this when it is all working
            #if os.path.exists(restore_to):
            #    shutil.rmtree(restore_to)
            pass
