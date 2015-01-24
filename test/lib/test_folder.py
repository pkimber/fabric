import os
import unittest

from lib.error import TaskError
from lib.folder import FolderInfo
from lib.siteinfo import SiteInfo


class TestFolderInfo(unittest.TestCase):

    def _site_info(self):
        module_folder = os.path.dirname(os.path.realpath(__file__))
        folder = os.path.join(module_folder, 'data', 'sites', 'data')
        folder = os.path.abspath(folder)
        return SiteInfo('drop-temp', 'csw_web', folder)

    def _site_info_testing(self):
        module_folder = os.path.dirname(os.path.realpath(__file__))
        folder = os.path.join(module_folder, 'data', 'sites', 'data_testing')
        folder = os.path.abspath(folder)
        return SiteInfo('drop-test', 'kb_couk', folder)

    def setUp(self):
        self.folder = FolderInfo(self._site_info())

    def test_folder_deploy(self):
        self.assertEquals(
            '/home/web/repo/project/csw_web/deploy',
            self.folder.deploy()
        )

    def test_folder_install(self):
        folder = FolderInfo(self._site_info(), '1.2.34')
        self.assertIn(
            '/home/web/repo/project/csw_web/deploy',
            folder.install()
        )

    def test_folder_install_temp(self):
        folder = FolderInfo(self._site_info(), '1.2.34')
        temp_folder = folder.install_temp()
        self.assertIn('/home/web/repo/project/csw_web/deploy', temp_folder)
        self.assertIn('temp', temp_folder)

    def test_folder_install_venv(self):
        folder = FolderInfo(self._site_info(), '1.2.34')
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

    def test_folder_vassals(self):
        self.assertSequenceEqual(
            ('/home/web/repo/uwsgi/vassals/csw_web.ini',),
            self.folder.vassals()
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
            '/srv/ssl/westcountrycoders.co.uk/ssl-unified.crt',
            self.folder.ssl_cert()
        )

    def test_ssl_server_key(self):
        self.assertEquals(
            '/srv/ssl/westcountrycoders.co.uk/server.key',
            self.folder.ssl_server_key()
        )

    def test_ssl_cert_folder(self):
        self.assertEquals(
            '/srv/ssl/westcountrycoders.co.uk',
            self.folder.ssl_cert_folder()
        )

    def test_ssl_cert_folder_testing(self):
        folder = FolderInfo(self._site_info_testing())
        self.assertEquals(
            '/srv/ssl/test.kbsoftware.co.uk',
            folder.ssl_cert_folder()
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
