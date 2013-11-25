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

    def __init__(self, prefix, site_name, pillar_folder=None, certificate_folder=None):
        # Some constants
        self.ALLOWED_HOSTS = 'allowed_hosts'
        self.DB_IP = 'db_ip'
        self.DB_PASS = 'db_pass'
        self.DOMAIN = 'domain'
        self.LAN = 'lan'
        self.MAILGUN_ACCESS_KEY = 'mailgun_access_key'
        self.MAILGUN_SERVER_NAME = 'mailgun_server_name'
        self.MEDIA_ROOT = 'media_root'
        self.SECRET_KEY = 'secret_key'
        self.SSL = 'ssl'
        self.UWSGI_PORT = 'uwsgi_port'
        # Use the default location if not supplied
        if certificate_folder:
            self.certificate_folder = certificate_folder
        else:
            self.certificate_folder = os.path.join(INFO_FOLDER, 'ssl-cert')
        if not pillar_folder:
            pillar_folder = os.path.join(INFO_FOLDER, 'pillar')
        sites = self._load(pillar_folder)
        self._verify_sites(sites)
        self.db_ip = self._get_db_ip(pillar_folder, prefix)
        self.media_root = self._get_media_root(site_name)
        self.site_info = self._get_site_info(site_name, sites)

    def _get_db_ip(self, pillar_folder, prefix):
        settings_file = os.path.join(
            pillar_folder, 'db', prefix, 'settings.sls'
        )
        if not os.path.isfile(settings_file):
            raise InfoError(
                "Cannot find: '{}' (this file should contain the IP "
                "address of the database server)".format(settings_file)
            )
        listen_address = None
        with open(settings_file, 'r') as f:
            data = yaml.load(f)
            settings = data.get('postgres_settings', None)
            if settings:
                listen_address = settings.get('listen_address', None)
        if not listen_address:
            raise InfoError(
                "Cannot find 'postgres_settings', 'listen_address' "
                "in: '{}'".format(settings_file)
            )
        if listen_address == 'localhost':
            return ''
        else:
            if self.is_valid_ip(listen_address):
                return str(listen_address)
            else:
                raise InfoError(
                    "'postgres_settings', 'listen_address' "
                    "is an invalid IP address: '{}'".format(settings_file)
                )

    def _get_media_root(self, site_name):
        return '/home/web/repo/project/{}/files/'.format(site_name)

    def _get_site_info(self, site_name, sites):
        if site_name not in sites:
            raise InfoError("Site '{}' not found in folder".format(site_name))
        return sites[site_name]

    def _get_setting(self, key):
        if key not in self.site_info:
            raise InfoError("No '{}' setting for site".format(key))
        return self.site_info[key]

    def is_valid_ip(self, ip):
        try:
            IP(str(ip))
            return True
        except ValueError:
            return False

    def _load(self, pillar_folder):
        sites_folder = os.path.join(pillar_folder, 'sites')
        result = {}
        file_list = glob.glob(os.path.join(sites_folder, '*.sls'))
        for name in file_list:
            with open(name, 'r') as f:
                data = yaml.load(f)
                file_result = self._parse(name, data)
                self._verify_no_duplicate_site(result, file_result)
                result.update(file_result)
        if not result:
            raise InfoError(
                "No sites found in folder: '{}'".format(sites_folder)
            )
        return result

    def _parse(self, file_name, data):
        site = data.get('sites')
        if not site:
            raise InfoError(
                "pillar file '{}' not in the correct format: {}".format(
                    file_name, data
                )
            )
        result = {}
        for key, settings in site.iteritems():
            result[key] = settings
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

    def _verify_lan_not_ssl(self, site_name, settings):
        """
        If installing to a LAN, then cannot use SSL.

        This is only because I haven't done the nginx settings yet!

        """
        if settings.get(self.SSL):
            raise InfoError(
                "site '{}' is set to run on a LAN, "
                "so cant use SSL".format(site_name)
            )

    def _verify_no_duplicate_uwsgi_ports(self, sites):
        ports = {}
        for site, settings in sites.items():
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

    def _verify_sites(self, sites):
        for site_name, settings in sites.items():
            if self.DB_PASS not in settings:
                raise InfoError(
                    "site '{}' does not have a database "
                    "password".format(site_name)
                )
            if self.DOMAIN not in settings:
                raise InfoError(
                    "site '{}' does not have a domain name".format(site_name)
                )
            if self.SSL not in settings:
                raise InfoError(
                    "site '{}' does not have SSL 'True' or "
                    "'False'".format(site_name)
                )
            if settings.get(self.LAN):
                self._verify_lan_not_ssl(site_name, settings)
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
            self.DB_IP.upper(): self.db_ip,
            self.DB_PASS.upper(): self.password(),
            self.DOMAIN.upper(): self.domain(),
            self.MAILGUN_ACCESS_KEY.upper(): 'abc',
            self.SSL.upper(): str(self.ssl()),
            self.MAILGUN_SERVER_NAME.upper(): 'def',
            self.MEDIA_ROOT.upper(): self.media_root,
            self.SECRET_KEY.upper(): 'jkl',
        }

    def domain(self):
        return self._get_setting(self.DOMAIN)

    def ssl(self):
        return self._get_setting(self.SSL)

    def password(self):
        return self._get_setting(self.DB_PASS)

    def ssl_cert(self):
        return self._ssl_cert(self.domain())

    def ssl_server_key(self):
        return self._ssl_server_key(self.domain())

    def uwsgi_port(self):
        return self._get_setting(self.UWSGI_PORT)
