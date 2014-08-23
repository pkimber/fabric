import fnmatch
import glob
import os
import yaml

from IPy import IP

from lib.dev.folder import (
    get_certificate_folder,
    get_pillar_folder,
)
from lib.error import TaskError

SSL_CERT_NAME = 'ssl-unified.crt'
SSL_SERVER_KEY = 'server.key'


class SiteInfo(object):

    def __init__(self, server_name, site_name, pillar_folder=None, certificate_folder=None):
        self._site_name = site_name
        # Use the default location if not supplied
        #info_folder = self._find_info_folder()
        if certificate_folder:
            self.certificate_folder = certificate_folder
        else:
            self.certificate_folder = get_certificate_folder()
        if not pillar_folder:
            pillar_folder = get_pillar_folder()
        self._server_name = server_name
        self._pillar_data = self._load_pillar(pillar_folder)
        self._verify_profile()
        self._verify_sites()
        self._verify_database_settings()
        self._media_root = self._get_media_root()
        # check the site exists in the pillar
        self._get_site()

    def _get_value(self, key, key_data):
        """Use 'pillar_data' from the class."""
        result = None
        data = self._get_pillar_data_none(key)
        if data:
            result = data[key_data]
        return result

    def _get_db_ip(self):
        if self._is_postgres():
            settings = self._get_pillar_data('postgres_settings')
            listen_address = settings['listen_address']
            if listen_address == 'localhost':
                return ''
            else:
                return str(listen_address)
        else:
            return 'no ip for non-postgres database'

    def _get_media_root(self):
        return '/home/web/repo/project/{}/files/'.format(self._site_name)

    def _get_pillar_data(self, key):
        result = self._get_pillar_data_none(key)
        if not result:
            raise TaskError(
                "Cannot find '{}' key in the pillar data.".format(key)
            )
        return result

    def _get_pillar_data_none(self, key):
        """Get data from the pillar (if it exists)."""
        return self._pillar_data.get(key, None)

    def _get_prefix(self):
        result = None
        django = self._get_pillar_data_none('django')
        if django:
            pip = self._get_pillar_data('pip')
            if 'prefix' not in pip:
                raise TaskError(
                    "'{}' not found in 'pip' pillar.".format('prefix')
                )
            result = pip['prefix']
        return result

    def _get_pypirc(self):
        result = None
        django = self._get_pillar_data_none('django')
        if django:
            pip = self._get_pillar_data('pip')
            if 'pypirc' not in pip:
                raise TaskError(
                    "'{}' not found in 'pip' pillar: {}".format('pypirc')
                )
            result = pip['pypirc']
        return result

    def _get_site(self):
        sites = self._get_pillar_data('sites')
        if self._site_name not in sites:
            raise TaskError(
                "site '{}' not found in pillar: {}".format(
                    self._site_name, sites.keys()
                )
            )
        return sites[self._site_name]

    def _get_setting(self, key):
        site = self._get_site()
        if key not in site:
            raise TaskError("No '{}' setting for site".format(key))
        return site.get(key)

    def _is_postgres(self):
        """do any of the sites use postgres"""
        result = False
        sites = self._get_pillar_data('sites')
        for name, settings in sites.items():
            database_type = settings['db_type']
            if database_type == 'psql':
                result = True
                break
        return result

    #def _is_valid_ip(self, ip):
    #    try:
    #        IP(str(ip))
    #        return True
    #    except ValueError:
    #        return False

    def _load_pillar(self, pillar_folder):
        result = {}
        with open(os.path.join(pillar_folder, 'top.sls'), 'r') as f:
            data = yaml.load(f.read())
            base = data.get('base')
            for k, v in base.iteritems():
                if fnmatch.fnmatch(self._server_name, k):
                    for name in v:
                        names = name.split('.')
                        file_name = os.path.join(pillar_folder, *names)
                        file_name = file_name + '.sls'
                        with open(file_name, 'r') as fa:
                            attr = yaml.load(fa.read())
                            if len(attr) > 1:
                                raise TaskError(
                                    "Unexpected state: 'sls' file contains more "
                                    "than one key: {}".format(file_name)
                                )
                            key = attr.iterkeys().next()
                            if key in result:
                                raise TaskError(
                                    "key '{}' is already contained in 'result'"
                                    ": {}".format(key, file_name)
                                )
                            result.update(attr)
        return result

    def _ssl_cert_folder(self, domain):
        return os.path.join(self.certificate_folder, domain)

    def _ssl_cert(self, domain):
        return os.path.join(
            self._ssl_cert_folder(domain),
            SSL_CERT_NAME
        )

    def _ssl_server_key(self, domain):
        return os.path.join(
            self._ssl_cert_folder(domain),
            SSL_SERVER_KEY
        )

    def _verify_profile(self):
        has_django = False
        has_php = False
        sites = self._get_pillar_data('sites')
        for name, settings in sites.items():
            profile = settings.get('profile', None)
            if profile:
                if profile == 'django':
                    has_django = True
                elif profile == 'php':
                    has_php = True
                else:
                    raise TaskError(
                        "unknown 'profile' for site '{}'"
                        "(should be 'django' or 'php')".format(name)
                    )
            else:
                raise TaskError(
                    "site must have a 'profile' ('django' or 'php')"
                    ": '{}'".format(name)
                )
        if has_django:
            django = self._get_pillar_data_none('django')
            if not django:
                raise TaskError(
                    "cannot find '{}' config key in the pillar "
                    "data.  The config is a global variable used by "
                    "salt when setting up server state".format('django')
                )
        if has_php:
            is_php = self._get_pillar_data_none('php')
            if not is_php:
                raise TaskError(
                    "cannot find '{}' config key in the pillar "
                    "data.  The config is a global variable used by "
                    "salt when setting up server state".format('php')
                )

    def _verify_has_ssl_certificate(self, domain):
        if not os.path.exists(self.certificate_folder):
            raise TaskError(
                "Folder for SSL certificates does not exist: {}".format(
                    self.certificate_folder
                )
            )
        cert_folder = self._ssl_cert_folder(domain)
        if not os.path.exists(cert_folder):
            raise TaskError(
                "{}: folder for SSL certificate does not exist: {}".format(
                    domain, cert_folder
                )
            )
        if not os.path.isdir(cert_folder):
            raise TaskError(
                "{}: expecting folder for SSL certificate at '{}'".format(
                    domain, cert_folder
                )
            )
        certificate = self._ssl_cert(domain)
        if not os.path.exists(certificate):
            raise TaskError(
                "{}: certificate file not found '{}'".format(domain, certificate)
            )
        server_key = self._ssl_server_key(domain)
        if not os.path.exists(server_key):
            raise TaskError(
                "{}: server key not found '{}'".format(domain, server_key)
            )

    def _verify_lan_not_ssl(self, settings):
        """
        If installing to a LAN, then cannot use SSL.

        This is only because I haven't done the nginx settings yet!

        """
        if settings.get('ssl'):
            raise TaskError(
                "site '{}' is set to run on a LAN, "
                "so can't use SSL".format(self._site_name)
            )

    def _verify_no_duplicate_uwsgi_ports(self, sites):
        ports = {}
        for site, settings in sites.items():
            is_php = settings.get('profile') == 'php'
            if not is_php:
                if 'uwsgi_port' not in settings:
                    raise TaskError(
                        "site '{}' does not have a uWSGI port".format(site)
                    )
                number = settings['uwsgi_port']
                if number in ports:
                    raise TaskError(
                        "site '{}' has the same uWSGI port number "
                        "as '{}'".format(site, ports[number])
                    )
                else:
                    ports[number] = site

    def _verify_no_duplicate_site(self, results, file_results):
        for site, settings in file_results.items():
            if site in results:
                raise TaskError(
                    "Duplicate site: '{}' is contained in more than one "
                    "pillar file".format(site)
                )

    def _verify_database_settings(self):
        has_mysql = False
        has_postgres = False
        sites = self._get_pillar_data('sites')
        for name, settings in sites.items():
            if 'db_pass' not in settings:
                raise TaskError(
                    "site '{}' does not have a database "
                    "password".format(name)
                )
            if 'db_type' not in settings:
                raise TaskError(
                    "site '{}' does not have a database "
                    "type".format(name)
                )
            if settings['db_type'] == 'mysql':
                has_mysql = True
            elif settings['db_type'] == 'psql':
                has_postgres = True
            else:
                raise TaskError(
                    "site '{}' has an unknown database "
                    "type: {}".format(name, settings['db_type'])
                )
        if has_mysql:
            self._verify_database_settings_mysql()
        if has_postgres:
            self._verify_database_settings_postgres()

    def _verify_database_settings_mysql(self):
        if not self._get_pillar_data_none('mysql_server'):
            raise TaskError(
                "Cannot find '{}' config in the pillar. "
                "The config is a global variable used by salt when setting "
                "up server state".format('mysql_server')
            )

    def _verify_database_settings_postgres(self):
        settings = self._get_pillar_data('postgres_settings')
        listen_address = settings.get('listen_address', None)
        if not listen_address:
            raise TaskError(
                "Cannot find 'postgres_settings', 'listen_address'."
            )
        # amazon rds uses a long host name, not an ip address
        #if listen_address == self.LOCALHOST:
        #    pass
        #else:
        #    if self._is_valid_ip(listen_address):
        #        pass
        #    else:
        #        raise TaskError(
        #            "'postgres_settings', 'listen_address' "
        #            "is an invalid IP address '{}'".format(listen_address)
        #        )
        # 02/07/2014 - not required if we are not installing a database server
        #if not pillar_data.get(self.POSTGRES_SERVER, None):
        #    raise TaskError(
        #        "Cannot find '{}' config in the pillar. "
        #        "The config is a global variable used by salt when setting "
        #        "up server state".format(self.POSTGRES_SERVER)
        #    )

    def _verify_sites(self):
        sites = self._get_pillar_data('sites')
        for name, settings in sites.items():
            if 'domain' not in settings:
                raise TaskError(
                    "site '{}' does not have a domain name".format(name)
                )
            if 'ssl' not in settings:
                raise TaskError(
                    "site '{}' does not have SSL 'True' or "
                    "'False'".format(name)
                )
            if settings.get('lan'):
                self._verify_lan_not_ssl(settings)
            if settings.get('ssl'):
                self._verify_has_ssl_certificate(settings.get('domain'))
        self._verify_no_duplicate_uwsgi_ports(sites)

    def env(self):
        """
        Return a dict suitable for use with the fabric 'shell_env' command

        Note: The mailgun data and secret key are not needed when running
        Django 'manage.py' tasks, so don't bother to get the information.
        For more info, see:
        http://stackoverflow.com/questions/15170637/effects-of-changing-djangos-secret-key

        Note: if the secret key is required in future - the '$' character can't
        be properly escapted by 'shell_env' command so use the
        'generate_secret_key' command from 'django-extensions' until you get
        one without the '$' character.
        """

        result = {
            'ALLOWED_HOSTS': self.domain(),
            'DB_IP': self._get_db_ip(),
            'DB_PASS': self.password(),
            'DEFAULT_FROM_EMAIL': 'test@pkimber.net',
            'DOMAIN': self.domain(),
            'FTP_STATIC_DIR': 'z1',
            'FTP_STATIC_URL': 'a1',
            'MAILGUN_ACCESS_KEY': 'abc',
            'MAILGUN_SERVER_NAME': 'def',
            'MANDRILL_API_KEY': 'b3',
            'MANDRILL_USER_NAME': 'b4',
            'MEDIA_ROOT': self._media_root,
            'RECAPTCHA_PRIVATE_KEY': 'pqr',
            'RECAPTCHA_PUBLIC_KEY': 'stu',
            'SECRET_KEY': 'jkl',
            'SENDFILE_ROOT': 'mno',
            'SSL': str(self.ssl()),
            'STRIPE_PUBLISH_KEY': 'stu',
            'STRIPE_SECRET_KEY': 'vwx',
        }
        if self.is_amazon:
            result.update({
                'AWS_S3_ACCESS_KEY_ID': self._get_value('amazon', 'aws_s3_access_key_id'),
                'AWS_S3_SECRET_ACCESS_KEY': self._get_value('amazon', 'aws_s3_secret_access_key'),
            })
        return result

    def db_user(self):
        """MySQL has a maximum length for a user name of 16 characters.

        If you need to set a shorter user name, use the pillar 'db_user'
        setting.

        """
        site = self._get_site()
        result = site.get('db_user')
        if not result:
            result = self._site_name
        if self.is_mysql() and len(result) > 16:
            raise TaskError(
                "maximum length of user name for mysql is 16 characters:"
                "{}".format(result)
            )
        return result

    def domain(self):
        return self._get_setting('domain')

    @property
    def is_amazon(self):
        return bool(self._get_value('amazon', 'aws_s3_access_key_id'))

    def is_django(self):
        return self._get_setting('profile') == 'django'

    def is_ftp(self):
        site = self._get_site()
        if 'ftp' in site:
            return site.get('ftp')
        else:
            return False

    def is_mysql(self):
        return self._get_setting('db_type') == 'mysql'

    def is_php(self):
        return self._get_setting('profile') == 'php'

    def is_postgres(self):
        return self._get_setting('db_type') == 'psql'

    def backup(self):
        return self._get_setting('backup')

    #def mail_template_type(self):
    #    result = None
    #    mail = self._get_setting(self.MAIL)
    #    if self.MAIL_TEMPLATE_TYPE in mail:
    #        result = mail[self.MAIL_TEMPLATE_TYPE]
    #    return result

    def packages(self):
        return self._get_setting('packages')

    def password(self):
        return self._get_setting('db_pass')

    def prefix(self):
        return self._get_prefix()

    def pypirc(self):
        return self._get_pypirc()

    def server_name(self):
        return self._server_name

    def site_name(self):
        return self._site_name

    def ssl(self):
        return self._get_setting('ssl')

    def ssl_cert(self):
        return self._ssl_cert(self.domain())

    def ssl_server_key(self):
        return self._ssl_server_key(self.domain())

    def uwsgi_port(self):
        return self._get_setting('uwsgi_port')
