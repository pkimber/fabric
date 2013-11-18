import getpass
import os
import string

from datetime import datetime


class PathError(Exception):

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr('%s, %s' % (self.__class__.__name__, self.value))


class Path(object):

    def __init__(self, name, file_type):
        name = self._remove_ssh_user(name)
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
        }
        self.allowed = string.letters + string.digits + '_'
        self.extension = self._get_extension(file_type)
        self.file_type = file_type
        self.name = '{0}_{1}_{2}'.format(
            name,
            datetime.now().strftime('%Y%m%d_%H%M%S'),
            self.user_name()
        )
        self.test_name = 'test_{0}_{1}'.format(
            name,
            self.user_name()
        )
        if not self._valid(self.name):
            raise PathError(
                'name contains invalid characters: {}'.format(self.name)
            )

    def _get_extension(self, file_type):
        if file_type in self.options:
            return self.options[file_type].get(self.EXTENSION)
        else:
            raise PathError("invalid file type: '{}'".format(file_type))

    def _remove_ssh_user(self, name):
        result = name
        if '@' in result:
            pos = result.find('@')
            result = result[pos + 1:]
        return result

    def _valid(self, value):
        return all(c in self.allowed for c in value)

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

    def local_file(self):
        return os.path.expanduser(self.remote_file())

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
