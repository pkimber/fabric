# -*- encoding: utf-8 -*-
import glob
import os
import shutil
import tempfile

from datetime import datetime

from fabric.api import (
    abort,
    local,
)
from fabric.colors import (
    cyan,
    yellow,
)
from fabric.context_managers import shell_env


class Duplicity(object):

    def __init__(self, site_info, backup_or_files):
        self.backup = False
        self.files = False
        if backup_or_files == 'backup':
            self.backup = True
        elif backup_or_files == 'files':
            self.files = True
        else:
            abort(
                "Only 'backup' and 'files' are valid operations for duplicity "
                "commands (not '{}')".format(backup_or_files)
            )
        self.backup_or_files = backup_or_files
        self.site_info = site_info

    def _find_sql(self, restore_to):
        result = None
        found = None
        match = glob.glob('{}/*.sql'.format(restore_to))
        for item in match:
            print item
            print os.path.basename(item)
            file_name, extension = os.path.splitext(os.path.basename(item))
            print file_name
            print datetime.strptime(file_name, '%Y%m%d_%H%M')
            file_date_time = datetime.strptime(file_name, '%Y%m%d_%H%M')
            if not found or file_date_time > found:
                found = file_date_time
                result = item
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
        print restore_to
        sql = self._find_sql(restore_to)
        pass

    def list_current(self):
        self._heading('list_current')
        local('duplicity collection-status {}'.format(self._repo()))

    def restore(self):
        self._heading('restore')
        # TODO Remove the next two lines when tested
        self._restore_database('/tmp/tmpuMPvXo')
        return
        try:
            restore_to = tempfile.mkdtemp()
            self._restore(restore_to)
            if self.backup:
                self._restore_database(restore_to)
        finally:
            # TODO Remove the next line when tested
            if not self.backup:
                if os.path.exists(restore_to):
                    shutil.rmtree(restore_to)
