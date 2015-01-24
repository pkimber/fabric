# -*- encoding: utf-8 -*-
import os
import shutil
import tempfile

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
        if not backup_or_files in ('backup', 'files'):
            abort(
                "Only 'backup' and 'files' are valid operations for duplicity "
                "commands (not '{}')".format(backup_or_files)
            )
        self.backup_or_files = backup_or_files
        self.site_info = site_info

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

    def list_current(self):
        self._heading('list_current')
        local('duplicity collection-status {}'.format(self._repo()))

    def restore(self):
        self._heading('restore')
        try:
            restore_to = tempfile.mkdtemp()
            env = {
                'PASSPHRASE': self.site_info.rsync_gpg_password,
            }
            with shell_env(**env):
                local('duplicity restore {} {}'.format(
                    self._repo(),
                    restore_to,
                ))
        finally:
            if os.path.exists(restore_to):
                shutil.rmtree(restore_to)
