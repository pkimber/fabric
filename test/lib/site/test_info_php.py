import os
import unittest

from lib.site.info import InfoError
from lib.site.info import SiteInfo


class TestSiteInfoPhp(unittest.TestCase):

    def _get_test_cert_folder(self, folder_name):
        module_folder = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(module_folder, folder_name)

    def _get_test_data_folder(self, folder_name):
        module_folder = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(module_folder, folder_name)

    def setUp(self):
        self.site_info = SiteInfo(
            'drop-temp',
            'hatherleigh_info',
            self._get_test_data_folder('data_php'),
            self._get_test_cert_folder('cert')
        )

    def test_is_mysql(self):
        self.assertEquals(True, self.site_info.is_mysql())

    def test_is_php(self):
        self.assertEquals(True, self.site_info.is_php())

    def test_packages(self):
        packages = self.site_info.packages()
        self.assertEqual(2, len(packages))
        expected = {
            'name': 'drupal',
            'tar': '--strip-components=1',
            'archive': 'drupal-6.29.tar.gz',
        }
        self.assertDictEqual(expected, packages[0])
        expected = {
            'name': 'date',
            'archive': 'date-6.x-2.9.tar.gz',
        }
        self.assertDictEqual(expected, packages[1])

    def test_mysql_db_username(self):
        self.assertEquals('hatherleigh_info', self.site_info.db_user())

    def test_mysql_db_username_too_long(self):
        site_info = SiteInfo(
            'drop-user',
            'very_long_site_name',
            self._get_test_data_folder('data_php'),
            self._get_test_cert_folder('cert')
        )
        with self.assertRaises(InfoError) as cm:
            site_info.db_user()
        self.assertIn(
            'maximum length of user name for mysql',
            cm.exception.value
        )
