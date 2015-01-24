# -*- encoding: utf-8 -*-
from fabric.api import (
    abort,
    local,
)
from fabric.colors import green


class Duplicity(object):

    def __init__(self, site_info, backup_or_files):
        if not backup_or_files in ('backup', 'files'):
            abort(
                "Only 'backup' and 'files' are valid operations for duplicity "
                "commands (not '{}')".format(backup_or_files)
            )
        self.backup_or_files = backup_or_files
        self.site_info = site_info

    def _repo(self):
        return '{}{}/{}'.format(
            self.site_info.rsync_ssh,
            self.site_info.site_name,
            self.backup_or_files,
        )

    def list_current(self):
        print(green("list: {} for {}").format(
            self.backup_or_files,
            self.site_info.site_name,
        ))
        local('duplicity collection-status {}'.format(self._repo()))
