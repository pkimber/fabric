import os
import unittest

from lib.site.info import InfoError
from lib.site.info import SiteInfo


class TestSiteInfo(unittest.TestCase):

    def _get_test_cert_folder(self, folder_name):
        module_folder = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(module_folder, folder_name)

    def _get_test_data_folder(self, folder_name):
        module_folder = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(module_folder, folder_name)

    def test_database_domain(self):
        site_info = SiteInfo(
            'drop-temp',
            'csw_web',
            self._get_test_data_folder('data'),
            self._get_test_cert_folder('cert')
        )
        self.assertIn('westcountrycoders.co.uk', site_info.domain())

    def test_database_domain_missing(self):
        with self.assertRaises(InfoError) as cm:
            SiteInfo(
                'drop-temp',
                'na',
                self._get_test_data_folder('data_missing_domain'),
                self._get_test_cert_folder('cert')
            )
        self.assertIn('does not have a domain', cm.exception.value)

    def test_database_missing_ip(self):
        with self.assertRaises(InfoError) as cm:
            SiteInfo(
                'drop-temp',
                'na',
                self._get_test_data_folder('data_missing_db_ip'),
                self._get_test_cert_folder('cert')
            )
        self.assertIn(
            "Cannot find 'postgres_settings', 'listen_address'",
            cm.exception.value
        )

    def test_database_missing_ip_file(self):
        with self.assertRaises(InfoError) as cm:
            SiteInfo(
                'drop-temp',
                'na',
                self._get_test_data_folder('data_missing_db_ip_file'),
                self._get_test_cert_folder('cert')
            )
        self.assertIn(
            "Cannot find",
            cm.exception.value
        )

    def test_database_ip_invalid(self):
        with self.assertRaises(InfoError) as cm:
            SiteInfo(
                'drop-temp',
                'csw_web',
                self._get_test_data_folder('data_db_ip_invalid'),
                self._get_test_cert_folder('cert')
            )
        self.assertIn(
            "is an invalid IP",
            cm.exception.value
        )

    def test_database_password(self):
        site_info = SiteInfo(
            'drop-temp',
            'csw_web',
            self._get_test_data_folder('data'),
            self._get_test_cert_folder('cert')
        )
        self.assertIn('myPassword', site_info.password())

    def test_database_password_missing(self):
        with self.assertRaises(InfoError) as cm:
            SiteInfo(
                'drop-temp',
                'na',
                self._get_test_data_folder('data_missing_pass'),
                self._get_test_cert_folder('cert')
            )
        self.assertIn('does not have a database password', cm.exception.value)

    def test_database_type_missing(self):
        with self.assertRaises(InfoError) as cm:
            SiteInfo(
                'drop-temp',
                'csw_web',
                self._get_test_data_folder('data_missing_db_type'),
                self._get_test_cert_folder('cert')
            )
        self.assertIn('does not have a database type', cm.exception.value)

    def test_env(self):
        site_info = SiteInfo(
            'drop-temp',
            'csw_web',
            self._get_test_data_folder('data'),
            self._get_test_cert_folder('cert')
        )
        expected = {
            'ALLOWED_HOSTS': 'westcountrycoders.co.uk',
            'DB_IP': '10.11.10.10',
            'DB_PASS': 'myPassword',
            'DOMAIN': 'westcountrycoders.co.uk',
            'SSL': 'True',
            'MAILGUN_ACCESS_KEY': 'abc',
            'MAILGUN_SERVER_NAME': 'def',
            'MEDIA_ROOT': '/home/web/repo/project/csw_web/files/',
            'SECRET_KEY': 'jkl',
            'SENDFILE_ROOT': 'mno',
        }
        self.assertDictEqual(expected, site_info.env())

    def test_env_ssl_false(self):
        site_info = SiteInfo(
            'drop-temp',
            'test_crm',
            self._get_test_data_folder('data'),
            self._get_test_cert_folder('cert')
        )
        expected = {
            'ALLOWED_HOSTS': 'westcountrycoders.co.uk',
            'DB_IP': '10.11.10.10',
            'DB_PASS': 'myPassword',
            'DOMAIN': 'westcountrycoders.co.uk',
            'SSL': 'False',
            'MAILGUN_ACCESS_KEY': 'abc',
            'MAILGUN_SERVER_NAME': 'def',
            'MEDIA_ROOT': '/home/web/repo/project/test_crm/files/',
            'SECRET_KEY': 'jkl',
            'SENDFILE_ROOT': 'mno',
        }
        self.assertDictEqual(expected, site_info.env())

    def test_ssl(self):
        site_info = SiteInfo(
            'drop-temp',
            'csw_web',
            self._get_test_data_folder('data'),
            self._get_test_cert_folder('cert')
        )
        self.assertEquals(True, site_info.ssl())

    def test_ssl_certificate_file(self):
        site_info = SiteInfo(
            'drop-temp',
            'csw_web',
            self._get_test_data_folder('data'),
            self._get_test_cert_folder('cert')
        )
        self.assertIn(
            'westcountrycoders.co.uk/ssl-unified.crt',
            site_info.ssl_cert()
        )

    def test_ssl_server_key(self):
        site_info = SiteInfo(
            'drop-temp',
            'csw_web',
            self._get_test_data_folder('data'),
            self._get_test_cert_folder('cert')
        )
        self.assertIn(
            'westcountrycoders.co.uk/server.key',
            site_info.ssl_server_key()
        )

    def test_ssl_missing(self):
        with self.assertRaises(InfoError) as cm:
            SiteInfo(
                'drop-temp',
                'na',
                self._get_test_data_folder('data_missing_ssl')
            )
        self.assertIn(
            "does not have SSL 'True' or 'False'",
            cm.exception.value
        )

    def test_ssl_missing_cert_folder(self):
        with self.assertRaises(InfoError) as cm:
            SiteInfo(
                'drop-temp',
                'csw_web',
                self._get_test_data_folder('data_missing_ssl_cert'),
                self._get_test_cert_folder('cert_folder_missing')
            )
        self.assertIn(
            "Folder for SSL certificates does not exist",
            cm.exception.value
        )

    def test_ssl_missing_site_cert_folder(self):
        with self.assertRaises(InfoError) as cm:
            SiteInfo(
                'drop-temp',
                'csw_web',
                self._get_test_data_folder('data_missing_ssl_cert'),
                self._get_test_cert_folder('cert_site_folder_missing')
            )
        self.assertIn(
            "folder for SSL certificate does not exist",
            cm.exception.value
        )

    def test_ssl_site_cert_folder_is_file(self):
        with self.assertRaises(InfoError) as cm:
            SiteInfo(
                'drop-temp',
                'csw_web',
                self._get_test_data_folder('data_missing_ssl_cert'),
                self._get_test_cert_folder('cert_site_folder_is_file')
            )
        self.assertIn(
            "expecting folder for SSL certificate",
            cm.exception.value
        )

    def test_ssl_site_cert_missing(self):
        with self.assertRaises(InfoError) as cm:
            SiteInfo(
                'drop-temp',
                'csw_web',
                self._get_test_data_folder('data_missing_ssl_cert'),
                self._get_test_cert_folder('cert_site_file_missing')
            )
        self.assertIn(
            "certificate file not found",
            cm.exception.value
        )

    def test_ssl_site_server_key_missing(self):
        with self.assertRaises(InfoError) as cm:
            SiteInfo(
                'drop-temp',
                'csw_web',
                self._get_test_data_folder('data_missing_ssl_cert'),
                self._get_test_cert_folder('cert_site_server_key_missing')
            )
        self.assertIn(
            "server key not found",
            cm.exception.value
        )

    def test_site_unknown(self):
        with self.assertRaises(InfoError) as cm:
            SiteInfo(
                'drop-temp',
                'cswsite_doesnotexist',
                self._get_test_data_folder('data'),
                self._get_test_cert_folder('cert')
            )
        self.assertIn('not found in folder', cm.exception.value)

    def test_lan_and_ssl(self):
        with self.assertRaises(InfoError) as cm:
            SiteInfo(
                'drop-temp',
                'na',
                self._get_test_data_folder('data_lan_and_ssl'),
                self._get_test_cert_folder('cert')
            )
        self.assertIn('LAN, so cant use SSL', cm.exception.value)

    def test_no_duplicate_uwsgi_ports(self):
        with self.assertRaises(InfoError) as cm:
            SiteInfo(
                'drop-temp',
                'na',
                self._get_test_data_folder('data_dup_uwsgi_port'),
                self._get_test_cert_folder('cert')
            )
        self.assertIn('has the same uWSGI port number', cm.exception.value)

    def test_no_duplicate_sites(self):
        """
        Cannot do this check as PyYAML doesn't throw an error when it finds a
        duplicate key:
        https://bitbucket.org/xi/pyyaml/issue/9/ignore-duplicate-keys-and-send-warning-or
        """
        self.assertTrue(True)

    def test_no_duplicate_sites_in_file(self):
        """
        Cannot do this check as PyYAML doesn't throw an error when it finds a
        duplicate key:
        https://bitbucket.org/xi/pyyaml/issue/9/ignore-duplicate-keys-and-send-warning-or
        """
        self.assertTrue(True)

    def test_no_sites(self):
        with self.assertRaises(InfoError) as cm:
            SiteInfo(
                'drop-temp',
                'na',
                self._get_test_data_folder('data_sites_do_not_exist'),
                self._get_test_cert_folder('cert')
            )
        self.assertIn("Cannot find 'sites' key", cm.exception.value)
