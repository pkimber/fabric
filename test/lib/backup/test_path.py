import getpass
import unittest

from datetime import datetime

from lib.backup.path import PathError
from lib.backup.path import Path


class TestPath(unittest.TestCase):

    def setUp(self):
        self.path = Path('csw_web', 'postgres')
        self.user = getpass.getuser()
        self.year = datetime.now().strftime('%Y')

    def test_backup_file_name(self):
        backup_file_name = self.path.backup_file_name()
        self.assertIn('csw_web_', backup_file_name)
        self.assertIn(self.user, backup_file_name)
        self.assertIn(self.year, backup_file_name)
        self.assertIn('sql', backup_file_name)

    def test_backup_file_name_postgres(self):
        backup_file_name = self.path.backup_file_name()
        self.assertIn('sql', backup_file_name)

    def test_backup_file_name_files(self):
        path = Path('csw_web', 'files')
        backup_file_name = path.backup_file_name()
        self.assertIn('tar.gz', backup_file_name)

    def test_backup_file_name_user(self):
        path = Path('raymond@csw_web', 'postgres')
        self.assertNotIn('raymond', path.backup_file_name())

    def test_database_name(self):
        database_name = self.path.database_name()
        self.assertNotIn('sql', database_name)

    def test_files_folder(self):
        self.assertEquals('/home/web/repo/files', self.path.files_folder())

    def test_invalid_name(self):
        with self.assertRaises(PathError) as cm:
            Path('csw_web_*', 'postgres')
        self.assertIn('invalid characters', cm.exception.value)

    def test_invalid_file_type(self):
        with self.assertRaises(PathError) as cm:
            Path('csw_web_', 'smartie')
        self.assertIn('invalid file type', cm.exception.value)

    def test_local_file_files(self):
        path = Path('csw_web', 'files')
        local_file = path.local_file()
        self.assertIn('/repo/backup/files/csw_web_', local_file)
        self.assertIn('.tar.gz', local_file)

    def test_local_file_postgres(self):
        local_file = self.path.local_file()
        self.assertIn('home', local_file)
        self.assertIn(self.user, local_file)
        self.assertIn('/repo/backup/postgres/csw_web_', local_file)
        self.assertIn('.sql', local_file)

    def test_remote_file_files(self):
        path = Path('csw_web', 'files')
        remote_file = path.remote_file()
        self.assertIn('/repo/backup/files/csw_web_', remote_file)
        self.assertIn('.tar.gz', remote_file)

    def test_remote_file_name_postgres(self):
        remote_file = self.path.remote_file()
        self.assertIn('/repo/backup/postgres/csw_web_', remote_file)
        self.assertIn('.sql', remote_file)

    def test_remote_folder_files(self):
        path = Path('csw_web', 'files')
        remote_folder = path.remote_folder()
        self.assertIn('/repo/backup/files', remote_folder)

    def test_remote_folder_postgres(self):
        remote_folder = self.path.remote_folder()
        self.assertIn('/repo/backup/postgres', remote_folder)

    def test_test_database_name(self):
        self.assertEquals(
            self.path.test_database_name(), 'test_csw_web_patrick'
        )

    def test_user_name(self):
        self.assertEquals(self.path.user_name(), self.user)
