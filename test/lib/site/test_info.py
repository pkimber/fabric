import os
import unittest

from lib.error import (
    SiteNotFoundError,
    TaskError,
)
from lib.site.info import SiteInfo


class TestSiteInfo(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None

    def _get_test_cert_folder(self, folder_name):
        module_folder = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(module_folder, folder_name)

    def _get_test_data_folder(self, folder_name):
        module_folder = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(module_folder, folder_name)

    def _info(self):
        """This pillar is set-up correctly."""
        return SiteInfo(
            'drop-temp',
            'csw_web',
            self._get_test_data_folder('data'),
            self._get_test_cert_folder('cert')
        )

    def test_database_missing_ip(self):
        with self.assertRaises(TaskError) as cm:
            SiteInfo(
                'drop-temp',
                'csw_web',
                self._get_test_data_folder('data_missing_db_ip'),
                self._get_test_cert_folder('cert')
            )
        self.assertIn(
            "Cannot find 'postgres_settings', 'listen_address'",
            cm.exception.value
        )

    def test_database_missing_ip_file(self):
        with self.assertRaises(TaskError) as cm:
            SiteInfo(
                'drop-temp',
                'csw_web',
                self._get_test_data_folder('data_missing_db_ip_file'),
                self._get_test_cert_folder('cert')
            )
        self.assertIn(
            "Cannot find",
            cm.exception.value
        )

    def test_database_password_missing(self):
        with self.assertRaises(TaskError) as cm:
            SiteInfo(
                'drop-temp',
                'csw_web',
                self._get_test_data_folder('data_missing_pass'),
                self._get_test_cert_folder('cert')
            )
        self.assertIn('does not have a database password', cm.exception.value)

    def test_database_type_invalid(self):
        with self.assertRaises(TaskError) as cm:
            SiteInfo(
                'drop-temp',
                'csw_web',
                self._get_test_data_folder('data_invalid_db_type'),
                self._get_test_cert_folder('cert')
            )
        self.assertIn('unknown database type', cm.exception.value)

    def test_database_type_missing(self):
        with self.assertRaises(TaskError) as cm:
            SiteInfo(
                'drop-temp',
                'csw_web',
                self._get_test_data_folder('data_missing_db_type'),
                self._get_test_cert_folder('cert')
            )
        self.assertIn('does not have a database type', cm.exception.value)

    def test_db_host(self):
        self.assertEquals('10.11.10.10', self._info().db_host)

    def test_db_pass(self):
        self.assertIn('myPassword', self._info().db_pass)

    def test_domain(self):
        self.assertIn('westcountrycoders.co.uk', self._info().domain)

    def test_domain_missing(self):
        with self.assertRaises(TaskError) as cm:
            SiteInfo(
                'drop-temp',
                'csw_web',
                self._get_test_data_folder('data_missing_domain'),
                self._get_test_cert_folder('cert')
            )
        self.assertIn('does not have a domain', cm.exception.value)

    def test_domain_test(self):
        info = SiteInfo(
            'drop-test',
            'kb_couk',
            self._get_test_data_folder('data_testing'),
            self._get_test_cert_folder('cert')
        )
        self.assertIn('test.kbsoftware.co.uk', info.domain)

    def test_env(self):
        expected = {
            'ALLOWED_HOSTS': 'westcountrycoders.co.uk',
            'AWS_S3_ACCESS_KEY_ID': 'APPLE',
            'AWS_S3_SECRET_ACCESS_KEY': 'PINEAPPLE',
            'DB_IP': '10.11.10.10',
            'DB_PASS': 'myPassword',
            'DEFAULT_FROM_EMAIL': 'test@pkimber.net',
            'DOMAIN': 'westcountrycoders.co.uk',
            'FTP_STATIC_DIR': 'z1',
            'FTP_STATIC_URL': 'a1',
            'MAILGUN_ACCESS_KEY': 'abc',
            'MAILGUN_SERVER_NAME': 'def',
            'MANDRILL_API_KEY': 'b3',
            'MANDRILL_USER_NAME': 'b4',
            'MEDIA_ROOT': '/home/web/repo/project/csw_web/files/',
            'RECAPTCHA_PRIVATE_KEY': 'pqr',
            'RECAPTCHA_PUBLIC_KEY': 'stu',
            'SECRET_KEY': 'jkl',
            'SENDFILE_ROOT': 'mno',
            'SSL': 'True',
            'STRIPE_PUBLISH_KEY': 'stu',
            'STRIPE_SECRET_KEY': 'vwx',
            'TESTING': 'False',
        }
        self.assertDictEqual(expected, self._info().env())

    def test_env_ssl_false(self):
        site_info = SiteInfo(
            'drop-temp',
            'test_crm',
            self._get_test_data_folder('data'),
            self._get_test_cert_folder('cert')
        )
        expected = {
            'ALLOWED_HOSTS': 'westcountrycoders.co.uk',
            'AWS_S3_ACCESS_KEY_ID': 'APPLE',
            'AWS_S3_SECRET_ACCESS_KEY': 'PINEAPPLE',
            'DB_IP': '10.11.10.10',
            'DB_PASS': 'myPassword',
            'DEFAULT_FROM_EMAIL': 'test@pkimber.net',
            'DOMAIN': 'westcountrycoders.co.uk',
            'FTP_STATIC_DIR': 'z1',
            'FTP_STATIC_URL': 'a1',
            'MAILGUN_ACCESS_KEY': 'abc',
            'MAILGUN_SERVER_NAME': 'def',
            'MANDRILL_API_KEY': 'b3',
            'MANDRILL_USER_NAME': 'b4',
            'MEDIA_ROOT': '/home/web/repo/project/test_crm/files/',
            'RECAPTCHA_PRIVATE_KEY': 'pqr',
            'RECAPTCHA_PUBLIC_KEY': 'stu',
            'SECRET_KEY': 'jkl',
            'SENDFILE_ROOT': 'mno',
            'SSL': 'False',
            'STRIPE_PUBLISH_KEY': 'stu',
            'STRIPE_SECRET_KEY': 'vwx',
            'TESTING': 'False',
        }
        self.assertDictEqual(expected, site_info.env())

    def test_find_server_name(self):
        self.assertEquals('drop-temp', self._info().server_name())

    def test_is_amazon(self):
        self.assertTrue(self._info().is_amazon)

    def test_is_amazon_not(self):
        site_info = SiteInfo(
            'drop-temp',
            'csw_web',
            self._get_test_data_folder('data_not_amazon'),
            self._get_test_cert_folder('cert')
        )
        self.assertFalse(site_info.is_amazon)

    def test_is_django(self):
        self.assertEquals(True, self._info().is_django())

    def test_is_ftp(self):
        self.assertEquals(False, self._info().is_ftp())

    def test_is_postgres(self):
        self.assertEquals(True, self._info().is_postgres())

    def test_is_testing(self):
        """The pillar uses the same sites for live and testing."""
        info = SiteInfo(
            'drop-test',
            'kb_couk',
            self._get_test_data_folder('data_testing'),
            self._get_test_cert_folder('cert')
        )
        self.assertTrue(info.is_testing)
        info = SiteInfo(
            'drop',
            'kb_couk',
            self._get_test_data_folder('data_testing'),
            self._get_test_cert_folder('cert')
        )
        self.assertFalse(info.is_testing)
        info = SiteInfo(
            'drop-test',
            'kbnot_couk',
            self._get_test_data_folder('data_testing'),
            self._get_test_cert_folder('cert')
        )
        self.assertFalse(info.is_testing)

    def test_is_testing_not(self):
        self.assertFalse(self._info().is_testing)

    def test_postgres_pass(self):
        self.assertEquals('my-pg-pass', self._info().postgres_pass)

    def test_prefix(self):
        info = self._info()
        self.assertEquals('pkimber', info.prefix())
        self.assertEquals('dev', info.pypirc())

    def test_ssl(self):
        self.assertEquals(True, self._info().ssl)

    def test_ssl_certificate_file(self):
        self.assertIn(
            'westcountrycoders.co.uk/ssl-unified.crt',
            self._info().ssl_cert()
        )

    def test_ssl_server_key(self):
        self.assertIn(
            'westcountrycoders.co.uk/server.key',
            self._info().ssl_server_key()
        )

    def test_ssl_missing(self):
        with self.assertRaises(TaskError) as cm:
            SiteInfo(
                'drop-temp',
                'csw_web',
                self._get_test_data_folder('data_missing_ssl')
            )
        self.assertIn(
            "does not have SSL 'True' or 'False'",
            cm.exception.value
        )

    def test_ssl_missing_cert_folder(self):
        with self.assertRaises(TaskError) as cm:
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
        with self.assertRaises(TaskError) as cm:
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
        with self.assertRaises(TaskError) as cm:
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
        with self.assertRaises(TaskError) as cm:
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
        with self.assertRaises(TaskError) as cm:
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
        with self.assertRaises(SiteNotFoundError) as cm:
            SiteInfo(
                'drop-temp',
                'cswsite_doesnotexist',
                self._get_test_data_folder('data'),
                self._get_test_cert_folder('cert')
            )
        self.assertIn(
            "site 'cswsite_doesnotexist' not found in pillar",
            cm.exception.value
        )

    def test_lan_and_ssl(self):
        with self.assertRaises(TaskError) as cm:
            SiteInfo(
                'drop-temp',
                'csw_fourteen',
                self._get_test_data_folder('data_lan_and_ssl'),
                self._get_test_cert_folder('cert')
            )
        self.assertIn("LAN, so can't use SSL", cm.exception.value)

    def test_no_duplicate_uwsgi_ports(self):
        with self.assertRaises(TaskError) as cm:
            SiteInfo(
                'drop-temp',
                'csw_marking',
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
        with self.assertRaises(TaskError) as cm:
            SiteInfo(
                'na',
                'na',
                self._get_test_data_folder('data_sites_do_not_exist'),
                self._get_test_cert_folder('cert')
            )
        self.assertIn("Cannot find 'sites' key", cm.exception.value)

    def test_url(self):
        info = self._info()
        self.assertEqual('https://westcountrycoders.co.uk/', info.url)

    def test_url_testing(self):
        info = SiteInfo(
            'drop-test',
            'kb_couk',
            self._get_test_data_folder('data_testing'),
            self._get_test_cert_folder('cert')
        )
        self.assertEqual('https://test.kbsoftware.co.uk/', info.url)
