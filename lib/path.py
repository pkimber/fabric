import getpass
import os
import string

from datetime import datetime

from lib.error import TaskError


class Path(object):

    def __init__(self, name, file_type):
        # name = self._remove_ssh_user(name)
        self.EXTENSION = 'extension'
        self.options = {
            'mysql': {
                self.EXTENSION: 'sql',
            },
            'postgres': {
                self.EXTENSION: 'sql',
            },
            'files': {
                self.EXTENSION: 'tar.gz',
            },
            'ftp': {
                self.EXTENSION: 'ftp.tar.gz',
            },
        }
        # self.allowed = string.letters + string.digits + '_'
        self.extension = self._get_extension(file_type)
        self.file_type = file_type
        self.name = '{0}_{1}_{2}'.format(
            name.replace('.', '_'),
            datetime.now().strftime('%Y%m%d_%H%M%S'),
            self.user_name()
        )
        self.test_name = 'test_{0}_{1}'.format(
            name.replace('.', '_'),
            self.user_name()
        )
        # if not self._valid(self.name):
        #     raise TaskError(
        #         'name contains invalid characters: {}'.format(self.name)
        #     )

    def _get_extension(self, file_type):
        if file_type in self.options:
            return self.options[file_type].get(self.EXTENSION)
        else:
            raise TaskError("invalid file type: '{}'".format(file_type))

    # def _remove_ssh_user(self, name):
    #     result = name
    #     if '@' in result:
    #         pos = result.find('@')
    #         result = result[pos + 1:]
    #     return result

    # def _valid(self, value):
    #     return all(c in self.allowed for c in value)

    def backup_file_name(self):
        return '{}.{}'.format(self.name, self.extension)

    def database_name(self):
        return self.name

    def files_folder(self):
        return os.path.join(
            '/',
            'home',
            'web',
            'repo',
            'files',
        )

    def ftp_folder(self, site_name):
        return os.path.join(
            '/',
            'home',
            site_name,
            'site',
        )

    def local_file(self):
        return os.path.expanduser(self.remote_file())

    def local_project_folder(self, site_name):
        return os.path.join(
            os.path.expanduser('~'),
            'dev',
            'project',
            site_name,
        )

    def local_project_folder_media(self, site_name):
        return os.path.join(
            self.local_project_folder(site_name),
            'media',
        )

    def local_project_folder_media_private(self, site_name):
        return os.path.join(
            self.local_project_folder(site_name),
            'media-private',
        )

    def php_folders(self):
        return [
            'images',
            'sites/all/libraries',
            'sites/all/modules',
            'sites/all/themes',
            'sites/default/files',
        ]

    def remote_file(self):
        return os.path.join(
            self.remote_folder(),
            self.backup_file_name(),
        )

    def remote_folder(self):
        return os.path.join(
            '~',
            'repo',
            'backup',
            self.file_type,
        )

    def test_database_name(self):
        return self.test_name

    def user_name(self):
        return getpass.getuser()
