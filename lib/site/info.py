import fnmatch
import glob
import os
import yaml

from IPy import IP


INFO_FOLDER = '../deploy/'
SSL_CERT_NAME = 'ssl-unified.crt'
SSL_SERVER_KEY = 'server.key'


class InfoError(Exception):

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr('%s, %s' % (self.__class__.__name__, self.value))


class SiteInfo(object):

    def __init__(self, server_name, site_name, pillar_folder=None, certificate_folder=None):
        self._site_name = site_name
        # Some constants
        self.ALLOWED_HOSTS = 'allowed_hosts'
        self.DB_IP = 'db_ip'
        self.DB_PASS = 'db_pass'
        self.DB_TYPE = 'db_type'
        self.DJANGO = 'django'
        self.DOMAIN = 'domain'
        self.LAN = 'lan'
        self.LISTEN_ADDRESS = 'listen_address'
        self.LOCALHOST = 'localhost'
        self.MAILGUN_ACCESS_KEY = 'mailgun_access_key'
        self.MAILGUN_SERVER_NAME = 'mailgun_server_name'
        self.MEDIA_ROOT = 'media_root'
        self.MYSQL_SERVER = 'mysql_server'
        self.PHP = 'php'
        self.POSTGRES_SERVER = 'postgres_server'
        self.POSTGRES_SETTINGS = 'postgres_settings'
        self.PROFILE = 'profile'
        self.PSQL = 'psql'
        self.SECRET_KEY = 'secret_key'
        self.SENDFILE_ROOT = 'sendfile_root'
        self.SITES = 'sites'
        self.SSL = 'ssl'
        self.UWSGI_PORT = 'uwsgi_port'
        # Use the default location if not supplied
        if certificate_folder:
            self.certificate_folder = certificate_folder
        else:
            self.certificate_folder = os.path.join(INFO_FOLDER, 'ssl-cert')
        if not pillar_folder:
            pillar_folder = os.path.join(INFO_FOLDER, 'pillar')
        pillar_data = self._load_pillar(pillar_folder, server_name)
        self._verify_profile(pillar_data)
        self._verify_sites(pillar_data)
        self._verify_database_settings(pillar_data)
        self._db_ip = self._get_db_ip(pillar_data)
        self._media_root = self._get_media_root()
        self._site_info = self._get_site_info(pillar_data)

    def _get_db_ip(self, pillar_data):
        if self._is_postgres(pillar_data):
            settings = self._get_pillar_data(pillar_data, self.POSTGRES_SETTINGS)
            listen_address = settings[self.LISTEN_ADDRESS]
            if listen_address == self.LOCALHOST:
                return ''
            else:
                return str(listen_address)
        else:
            return 'no ip for non-postgres database'

    def _get_media_root(self):
        return '/home/web/repo/project/{}/files/'.format(self._site_name)

    def _get_pillar_data(self, pillar_data, key):
        result = pillar_data.get(key, None)
        if not result:
            raise InfoError(
                "Cannot find '{}' key in the pillar data.".format(key)
            )
        return result

    def _get_site_info(self, pillar_data):
        sites = self._get_pillar_data(pillar_data, self.SITES)
        if self._site_name not in sites:
            raise InfoError(
                "site '{}' not found in folder: {}".format(
                    self._site_name, sites.keys()
                )
            )
        return sites[self._site_name]

    def _get_setting(self, key):
        if key not in self._site_info:
            raise InfoError("No '{}' setting for site".format(key))
        return self._site_info[key]

    def _is_postgres(self, pillar_data):
        """do any of the sites use postgres"""
        result = False
        sites = self._get_pillar_data(pillar_data, self.SITES)
        for name, settings in sites.items():
            database_type = settings[self.DB_TYPE]
            if database_type == self.PSQL:
                result = True
                break
        return result

    def _is_valid_ip(self, ip):
        try:
            IP(str(ip))
            return True
        except ValueError:
            return False

    def _load_pillar(self, pillar_folder, server_name):
        result = {}
        with open(os.path.join(pillar_folder, 'top.sls'), 'r') as f:
            data = yaml.load(f.read())
            base = data.get('base')
            for k, v in base.iteritems():
                if fnmatch.fnmatch(server_name, k):
                    for name in v:
                        names = name.split('.')
                        file_name = os.path.join(pillar_folder, *names)
                        file_name = file_name + '.sls'
                        with open(file_name, 'r') as fa:
                            attr = yaml.load(fa.read())
                            if len(attr) > 1:
                                raise InfoError(
                                    "Unexpected state: 'sls' file contains more "
                                    "than one key: {}".format(file_name)
                                )
                            key = attr.iterkeys().next()
                            if key in result:
                                raise InfoError(
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

    def _verify_profile(self, pillar_data):
        has_django = False
        has_php = False
        sites = self._get_pillar_data(pillar_data, self.SITES)
        for name, settings in sites.items():
            profile = settings.get(self.PROFILE, None)
            if profile:
                if profile == self.DJANGO:
                    has_django = True
                elif profile == self.PHP:
                    has_php = True
                else:
                    raise InfoError(
                        "unknown 'profile' for site '{}'"
                        "(should be 'django' or 'php')".format(name)
                    )
            else:
                raise InfoError(
                    "site must have a 'profile' ('django' or 'php')"
                    ": '{}'".format(name)
                )
        if has_django:
            is_django = pillar_data.get(self.DJANGO, None)
            if not is_django:
                raise InfoError(
                    "cannot find '{}' config key in the pillar "
                    "data.  The config is a global variable used by "
                    "salt when setting up server state".format(self.DJANGO)
                )
        if has_php:
            is_php = pillar_data.get(self.PHP, None)
            if not is_php:
                raise InfoError(
                    "cannot find '{}' config key in the pillar "
                    "data.  The config is a global variable used by "
                    "salt when setting up server state".format(self.PHP)
                )

    def _verify_has_ssl_certificate(self, domain):
        if not os.path.exists(self.certificate_folder):
            raise InfoError(
                "Folder for SSL certificates does not exist: {}".format(
                    self.certificate_folder
                )
            )
        cert_folder = self._ssl_cert_folder(domain)
        if not os.path.exists(cert_folder):
            raise InfoError(
                "{}: folder for SSL certificate does not exist: {}".format(
                    domain, cert_folder
                )
            )
        if not os.path.isdir(cert_folder):
            raise InfoError(
                "{}: expecting folder for SSL certificate at '{}'".format(
                    domain, cert_folder
                )
            )
        certificate = self._ssl_cert(domain)
        if not os.path.exists(certificate):
            raise InfoError(
                "{}: certificate file not found '{}'".format(domain, certificate)
            )
        server_key = self._ssl_server_key(domain)
        if not os.path.exists(server_key):
            raise InfoError(
                "{}: server key not found '{}'".format(domain, server_key)
            )

    def _verify_lan_not_ssl(self, settings):
        """
        If installing to a LAN, then cannot use SSL.

        This is only because I haven't done the nginx settings yet!

        """
        if settings.get(self.SSL):
            raise InfoError(
                "site '{}' is set to run on a LAN, "
                "so can't use SSL".format(self._site_name)
            )

    def _verify_no_duplicate_uwsgi_ports(self, sites):
        ports = {}
        for site, settings in sites.items():
            is_php = settings.get(self.PROFILE) == self.PHP
            if not is_php:
                if self.UWSGI_PORT not in settings:
                    raise InfoError(
                        "site '{}' does not have a uWSGI port".format(site)
                    )
                number = settings[self.UWSGI_PORT]
                if number in ports:
                    raise InfoError(
                        "site '{}' has the same uWSGI port number "
                        "as '{}'".format(site, ports[number])
                    )
                else:
                    ports[number] = site

    def _verify_no_duplicate_site(self, results, file_results):
        for site, settings in file_results.items():
            if site in results:
                raise InfoError(
                    "Duplicate site: '{}' is contained in more than one "
                    "pillar file".format(site)
                )

    def _verify_database_settings(self, pillar_data):
        has_mysql = False
        has_postgres = False
        sites = self._get_pillar_data(pillar_data, self.SITES)
        for name, settings in sites.items():
            if self.DB_PASS not in settings:
                raise InfoError(
                    "site '{}' does not have a database "
                    "password".format(name)
                )
            if self.DB_TYPE not in settings:
                raise InfoError(
                    "site '{}' does not have a database "
                    "type".format(name)
                )
            if settings[self.DB_TYPE] == 'mysql':
                has_mysql = True
            elif settings[self.DB_TYPE] == self.PSQL:
                has_postgres = True
            else:
                raise InfoError(
                    "site '{}' has an unknown database "
                    "type: {}".format(name, settings[self.DB_TYPE])
                )
        if has_mysql:
            self._verify_database_settings_mysql(pillar_data)
        if has_postgres:
            self._verify_database_settings_postgres(pillar_data)

    def _verify_database_settings_mysql(self, pillar_data):
        if not pillar_data.get(self.MYSQL_SERVER, None):
            raise InfoError(
                "Cannot find '{}' config in the pillar. "
                "The config is a global variable used by salt when setting "
                "up server state".format(self.MYSQL_SERVER)
            )

    def _verify_database_settings_postgres(self, pillar_data):
        settings = self._get_pillar_data(pillar_data, self.POSTGRES_SETTINGS)
        listen_address = settings.get(self.LISTEN_ADDRESS, None)
        if not listen_address:
            raise InfoError(
                "Cannot find 'postgres_settings', 'listen_address'."
            )
        if listen_address == self.LOCALHOST:
            pass
        else:
            if self._is_valid_ip(listen_address):
                pass
            else:
                raise InfoError(
                    "'postgres_settings', 'listen_address' "
                    "is an invalid IP address '{}'".format(listen_address)
                )
        if not pillar_data.get(self.POSTGRES_SERVER, None):
            raise InfoError(
                "Cannot find '{}' config in the pillar. "
                "The config is a global variable used by salt when setting "
                "up server state".format(self.POSTGRES_SERVER)
            )

    def _verify_sites(self, pillar_data):
        sites = self._get_pillar_data(pillar_data, self.SITES)
        for name, settings in sites.items():
            if self.DOMAIN not in settings:
                raise InfoError(
                    "site '{}' does not have a domain name".format(name)
                )
            if self.SSL not in settings:
                raise InfoError(
                    "site '{}' does not have SSL 'True' or "
                    "'False'".format(name)
                )
            if settings.get(self.LAN):
                self._verify_lan_not_ssl(settings)
            if settings.get(self.SSL):
                self._verify_has_ssl_certificate(settings.get(self.DOMAIN))
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
        return {
            self.ALLOWED_HOSTS.upper(): self.domain(),
            self.DB_IP.upper(): self._db_ip,
            self.DB_PASS.upper(): self.password(),
            self.DOMAIN.upper(): self.domain(),
            self.MAILGUN_ACCESS_KEY.upper(): 'abc',
            self.SSL.upper(): str(self.ssl()),
            self.MAILGUN_SERVER_NAME.upper(): 'def',
            self.MEDIA_ROOT.upper(): self._media_root,
            self.SECRET_KEY.upper(): 'jkl',
            self.SENDFILE_ROOT.upper(): 'mno',
        }

    def domain(self):
        return self._get_setting(self.DOMAIN)

    def is_django(self):
        return self._get_setting(self.PROFILE) == self.DJANGO

    def is_php(self):
        return self._get_setting(self.PROFILE) == self.PHP

    def packages(self):
        return self._get_setting('packages')

    def ssl(self):
        return self._get_setting(self.SSL)

    def password(self):
        return self._get_setting(self.DB_PASS)

    def site_name(self):
        return self._site_name

    def ssl_cert(self):
        return self._ssl_cert(self.domain())

    def ssl_server_key(self):
        return self._ssl_server_key(self.domain())

    def uwsgi_port(self):
        return self._get_setting(self.UWSGI_PORT)
