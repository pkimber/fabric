import unittest

from lib.error import TaskError
from lib.server.folder import FolderInfo


class TestFolderInfo(unittest.TestCase):

    def setUp(self):
        self.folder = FolderInfo('csw_web')

    def test_folder_deploy(self):
        self.assertEquals(
            '/home/web/repo/project/csw_web/deploy',
            self.folder.deploy()
        )

    def test_folder_install(self):
        folder = FolderInfo('csw_web', '1.2.34')
        self.assertIn(
            '/home/web/repo/project/csw_web/deploy',
            folder.install()
        )

    def test_folder_install_temp(self):
        folder = FolderInfo('csw_web', '1.2.34')
        temp_folder = folder.install_temp()
        self.assertIn('/home/web/repo/project/csw_web/deploy', temp_folder)
        self.assertIn('temp', temp_folder)

    def test_folder_install_venv(self):
        folder = FolderInfo('csw_web', '1.2.34')
        folder_name = folder.install_venv()
        self.assertIn('/home/web/repo/project/csw_web/deploy', folder_name)
        self.assertIn('venv', folder_name)

    def test_folder_live(self):
        self.assertEquals(
            '/home/web/repo/project/csw_web/live',
            self.folder.live()
        )

    def test_folder_site(self):
        self.assertEquals(
            '/home/web/repo/project/csw_web',
            self.folder.site()
        )

    def test_folder_vassal(self):
        self.assertEquals(
            '/home/web/repo/uwsgi/vassals/csw_web.ini',
            self.folder.vassal()
        )

    def test_invalid_folder_version(self):
        with self.assertRaises(TaskError) as cm:
            self.folder.install()
        self.assertIn(
            "class wasn't constructed with a version number",
            cm.exception.value
        )

    def test_ssl_cert(self):
        self.assertEquals(
            '/srv/ssl/csw_web/ssl-unified.crt',
            self.folder.ssl_cert()
        )

    def test_ssl_server_key(self):
        self.assertEquals(
            '/srv/ssl/csw_web/server.key',
            self.folder.ssl_server_key()
        )

    def test_ssl_cert_folder(self):
        self.assertEquals(
            '/srv/ssl/csw_web',
            self.folder.ssl_cert_folder()
        )

    def test_ssl_folder(self):
        self.assertEquals(
            '/srv/ssl',
            self.folder.ssl_folder()
        )

    def test_srv_folder(self):
        self.assertEquals(
            '/srv',
            self.folder.srv_folder()
        )
