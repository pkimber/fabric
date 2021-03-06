import fnmatch
import os
import yaml

from lib.error import SiteNotFoundError, TaskError
from lib.folder import get_pillar_folder, SSL_CERT_NAME, SSL_SERVER_KEY


class SiteInfo(object):

    def __init__(self, minion_id, domain, pillar_folder=None):
        self._minion_id = minion_id
        self._domain = domain
        self._pillar_folder = pillar_folder or get_pillar_folder()
        self._pillar = self._load()
        self._media_root = self._get_media_root()
        self._verify_profile()
        self._verify_sites()
        self._verify_site()
        self._verify_database_settings()

    def _get_media_root(self):
        return '/home/web/repo/project/{}/files/'.format(self._domain)

    def _get(self, key):
        result = self._get_none(key)
        if not result:
            raise TaskError(
                "Cannot find '{}' key in the pillar data".format(key)
            )
        return result

    def _get_env(self):
        """Extra environment variables."""
        site = self._get_site()
        env = site.get('env', {})
        result = {}
        for key, value in env.items():
            result[key.upper()] = str(value)
        return result

    def _get_none(self, key):
        """Get data from the pillar (if it exists)."""
        return self._pillar.get(key, None)

    def _get_prefix(self):
        result = None
        django = self._get_none('django')
        if django:
            pip = self._get('pip')
            if 'prefix' not in pip:
                raise TaskError(
                    "'{}' not found in 'pip' pillar.".format('prefix')
                )
            result = pip['prefix']
        return result

    def _get_pypirc(self):
        result = None
        django = self._get_none('django')
        if django:
            pip = self._get('pip')
            if 'pypirc' not in pip:
                raise TaskError(
                    "'{}' not found in 'pip' pillar: {}".format('pypirc')
                )
            result = pip['pypirc']
        return result

    def _get_site(self):
        sites = self._get('sites')
        if self._domain not in sites:
            raise SiteNotFoundError(
                "domain '{}' not found in pillar: {}".format(
                    self._domain, sites.keys()
                )
            )
        return sites[self._domain]

    def _get_setting(self, key):
        site = self._get_site()
        if key not in site:
            raise TaskError(
                "No '{}' setting for site: {}".format(key, site.keys())
            )
        return site.get(key)

    def _is_postgres_server(self):
        """do any of the sites use postgres"""
        result = False
        sites = self._get('sites')
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

    def _load(self):
        result = {}
        with open(os.path.join(self._pillar_folder, 'top.sls'), 'r') as f:
            data = yaml.load(f.read())
            base = data.get('base')
            for k, v in base.items():
                # unix style file-name match
                if self._match(self._minion_id, k):
                    for name in v:
                        if isinstance(name, dict):
                            # top.sls file has a dict e.g. '- match: list'
                            pass
                        else:
                            attr = self._parse(name)
                            # will contain no more than one key (see above)
                            for key in attr.keys():
                                if key in result:
                                    raise TaskError(
                                        "key '{}' is already contained in "
                                        "'{}".format(key, self._minion_id)
                                    )
                            result.update(attr)
        return result

    def _match(self, minion_id, salt_top):
        result = fnmatch.fnmatch(minion_id, salt_top)
        if not result:
            for item in salt_top.split(','):
                result = fnmatch.fnmatch(minion_id, item)
                if result:
                    break
        return result

    def _parse(self, config):
        """Parse the config from the 'top.sls' file.

        e.g::

          - config.django
          - config.nginx

        """
        names = config.split('.')
        file_name = os.path.join(self._pillar_folder, *names)
        file_name = file_name + '.sls'
        with open(file_name, 'r') as fa:
            attr = yaml.load(fa.read())
            if len(attr) > 1:
                raise TaskError(
                    "Unexpected state: 'sls' file contains more "
                    "than one key: {}".format(file_name)
                )
        return attr

    def _ssl_cert(self, domain):
        return os.path.join(
            self._ssl_cert_folder(domain),
            SSL_CERT_NAME
        )

    def _ssl_cert_folder(self, domain):
        return os.path.join(self.certificate_folder, domain)

    def ssl_cert(self):
        return self._ssl_cert(self._domain)

    def _ssl_server_key(self, domain):
        return os.path.join(
            self._ssl_cert_folder(domain),
            SSL_SERVER_KEY
        )

    def ssl_server_key(self):
        return self._ssl_server_key(self._domain)

    def _verify_profile(self):
        has_django = False
        has_php = False
        try:
            sites = self._get('sites')
        except TaskError:
            raise SiteNotFoundError(
                "pillar has no 'sites' key for server '{}', domain '{}'"
                ".".format(self._minion_id, self._domain)
            )
        for name, settings in sites.items():
            profile = settings.get('profile', None)
            if profile:
                if profile == 'django':
                    has_django = True
                elif profile == 'mattermost':
                    pass
                elif profile in ('php', 'apache_php'):
                    has_php = True
                else:
                    raise TaskError(
                        "unknown 'profile' for site '{}'"
                        "(should be 'django', 'apache_php' or 'php')".format(name)
                    )
            else:
                raise TaskError(
                    "site must have a 'profile' ('django' or 'php')"
                    ": '{}'".format(name)
                )
        if has_django:
            django = self._get_none('django')
            if not django:
                raise TaskError(
                    "cannot find '{}' config key in the pillar "
                    "data.  The config is a global variable used by "
                    "salt when setting up server state".format('django')
                )
        if has_php:
            is_php = self._get_none('php') or self._get_none('apache_php')
            if not is_php:
                raise TaskError(
                    "cannot find '{}' config key in the pillar "
                    "data.  The config is a global variable used by "
                    "salt when setting up server state".format('php')
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
            profile = settings.get('profile')
            is_mattermost = profile == 'mattermost'
            is_php = profile in ('php', 'apache_php')
            if not is_mattermost and not is_php:
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
        server_has_mysql = False
        server_has_postgres = False
        sites = self._get('sites')
        for name, settings in sites.items():
            site_has_mysql = False
            site_has_postgres = False
            if 'db_type' not in settings:
                raise TaskError(
                    "site '{}' does not have a database "
                    "type".format(name)
                )
            if settings['db_type'] == 'mysql':
                server_has_mysql = True
                site_has_mysql = True
            elif settings['db_type'] == 'psql':
                server_has_postgres = True
                site_has_postgres = True
            elif settings['db_type'] == '':
                pass
            else:
                raise TaskError(
                    "site '{}' has an unknown database "
                    "type: {}".format(name, settings['db_type'])
                )
            if site_has_postgres or site_has_mysql:
                if 'db_pass' not in settings:
                    raise TaskError(
                        "site '{}' does not have a database "
                        "password".format(name)
                    )
        if server_has_mysql:
            self._verify_database_settings_mysql()
        if server_has_postgres:
            self._verify_database_settings_postgres()

    def _verify_database_settings_mysql(self):
        if not self._get_none('mysql_server'):
            raise TaskError(
                "Cannot find '{}' config in the pillar. "
                "The config is a global variable used by salt when setting "
                "up server state".format('mysql_server')
            )

    def _verify_database_settings_postgres(self):
        settings = self._get('postgres_settings')
        listen_address = settings.get('listen_address', None)
        postgres_pass = settings.get('postgres_pass', None)
        if not listen_address:
            raise TaskError(
                "Cannot find 'postgres_settings', "
                "'listen_address'.".format(self._pillar_folder)
            )
        if listen_address == 'localhost':
            pass
        else:
            if not postgres_pass:
                raise TaskError(
                    "Cannot find 'postgres_settings', 'postgres_pass' "
                    "in pillar '{}'".format(self._pillar_folder)
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

    def _verify_site(self):
        self._get_site()

    def _verify_sites(self):
        sites = self._get('sites')
        for domain, settings in sites.items():
            if 'ssl' not in settings:
                raise TaskError(
                    "site '{}' does not have SSL 'True' or "
                    "'False'".format(domain)
                )
            if settings.get('lan'):
                self._verify_lan_not_ssl(settings)
        self._verify_no_duplicate_uwsgi_ports(sites)

    def env(self):
        """Return a dict suitable for use with the fabric 'shell_env' command.

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
            'ALLOWED_HOSTS': self.domain,
            'DEFAULT_FROM_EMAIL': 'test@pkimber.net',
            'DOMAIN': self.domain,
            'FTP_STATIC_DIR': 'z1',
            'FTP_STATIC_URL': 'a1',
            'HOST_NAME': 'blue',
            'MAILGUN_ACCESS_KEY': 'abc',
            'MAILGUN_SERVER_NAME': 'def',
            'MANDRILL_API_KEY': 'b3',
            'MANDRILL_USER_NAME': 'b4',
            'MEDIA_ROOT': self._media_root,
            'NORECAPTCHA_SECRET_KEY': 'pqr',
            'NORECAPTCHA_SITE_KEY': 'stu',
            'OPBEAT_APP_ID': '123',
            'OPBEAT_ORGANIZATION_ID': '123',
            'OPBEAT_SECRET_TOKEN': '123',
            'SECRET_KEY': 'jkl',
            'SENDFILE_ROOT': 'mno',
            'SSL': str(self.ssl),
            'STRIPE_PUBLISH_KEY': 'stu',
            'STRIPE_SECRET_KEY': 'vwx',
            'TESTING': str(self.is_testing),
        }
        if self.has_database:
            result.update({
                'DB_IP': self.db_host,
                'DB_PASS': self.db_pass,
            })
        # extra env variables
        result.update(self._get_env())
        if self.is_amazon:
            amazon = self._get('amazon')
            result.update({
                'AWS_S3_ACCESS_KEY_ID': amazon.get('aws_s3_access_key_id'),
                'AWS_S3_SECRET_ACCESS_KEY': amazon.get('aws_s3_secret_access_key'),
            })
        return result

    @property
    def compress(self):
        """Use Compressor with Amazon unless 'compress' flag is set 'False'."""
        site = self._get_site()
        result = site.get('compress', True)
        return result and self.is_amazon

    @property
    def db_host(self):
        if self._is_postgres_server():
            settings = self._get('postgres_settings')
            listen_address = settings['listen_address']
            if listen_address == 'localhost':
                return ''
            else:
                return str(listen_address)
        else:
            raise TaskError('no ip for non-postgres database')

    @property
    def db_name(self):
        return self._domain.replace('.', '_')

    @property
    def db_name_workflow(self):
        return '{}_workflow'.format(self._domain.replace('.', '_'))

    @property
    def db_pass(self):
        return self._get_setting('db_pass')

    @property
    def db_user(self):
        """MySQL has a maximum length for a user name of 16 characters.

        If you need to set a shorter user name, use the pillar 'db_user'
        setting.

        """
        site = self._get_site()
        result = site.get('db_user')
        if not result:
            result = self._site_name
        if self.is_mysql and len(result) > 16:
            raise TaskError(
                "maximum length of user name for mysql is 16 characters:"
                "{}".format(result)
            )
        return result

    @property
    def domain(self):
        return self._domain

    @property
    def is_amazon(self):
        # keys are set in 'global/amazon.sls'
        amazon_key = bool(self._get_none('amazon'))
        # does this site use amazon?
        amazon_site = False
        site = self._get_site()
        if 'amazon' in site:
            amazon_site = site.get('amazon')
        # check we have keys if the site is using amazon
        if amazon_site and not amazon_key:
            raise TaskError(
                "The site is using 'amazon', but we have no keys!"
            )
        return amazon_key and amazon_site

    @property
    def is_celery(self):
        site = self._get_site()
        if 'celery' in site:
            return site.get('celery')
        else:
            return False

    def is_django(self):
        return self._get_setting('profile') == 'django'

    def is_ftp(self):
        site = self._get_site()
        if 'ftp' in site:
            return site.get('ftp')
        else:
            return False

    @property
    def is_mysql(self):
        return self._get_setting('db_type') == 'mysql'

    @property
    def is_php(self):
        return self._get_setting('profile') in ('php', 'apache_php')

    @property
    def is_postgres(self):
        return self._get_setting('db_type') == 'psql'

    @property
    def is_testing(self):
        """server and the site must be set-up for testing."""
        result = bool(self._get_none('testing'))
        if result:
            result = 'test' in self._get_site()
        return result

    @property
    def is_workflow(self):
        site = self._get_site()
        if 'workflow' in site:
            return site.get('workflow')
        else:
            return False

    def backup(self):
        return self._get_setting('backup')

    #def mail_template_type(self):
    #    result = None
    #    mail = self._get_setting(self.MAIL)
    #    if self.MAIL_TEMPLATE_TYPE in mail:
    #        result = mail[self.MAIL_TEMPLATE_TYPE]
    #    return result

    @property
    def has_database(self):
        db_type = self._get_setting('db_type')
        if db_type in ('psql', 'mysql'):
            result = True
        elif db_type == '':
            result = False
        else:
            # this should already be checked in '_verify_database_settings'
            raise TaskError(
                "site '{}' has an unknown database "
                "type: {}".format(self._site_name, db_type)
            )
        return result

    def packages(self):
        return self._get_setting('packages')

    @property
    def postgres_pass(self):
        if self._is_postgres_server():
            settings = self._get('postgres_settings')
            return settings.get('postgres_pass')
        else:
            raise TaskError('no password for non-postgres database')

    def prefix(self):
        return self._get_prefix()

    def pypirc(self):
        return self._get_pypirc()

    def rsync(self):
        gpg = self._get_none('gpg')
        if not gpg:
            raise TaskError('no gpg information found')
        rsync = gpg.get('rsync')
        if not rsync:
            raise TaskError('no rsync information found in gpg')
        return rsync

    @property
    def rsync_gpg_password(self):
        rsync = self.rsync()
        key = rsync.get('pass')
        if not key:
            raise TaskError('no gpg password found in rsync')
        return key

    @property
    def rsync_ssh(self):
        rsync = self.rsync()
        server = rsync.get('server')
        if not server:
            raise TaskError('no rsync server found in rsync')
        user = rsync.get('user')
        if not user:
            raise TaskError('no rsync user found in rsync')
        # if I change this to 'scp' will it just work?
        return 'scp://{}@{}/'.format(user, server)

    def minion_id(self):
        return self._minion_id

    @property
    def package(self):
        return self._get_setting('package')

    @property
    def ssl(self):
        return self._get_setting('ssl')

    @property
    def url(self):
        return '{}://{}/'.format(
            'https' if self.ssl else 'http',
            self.domain,
        )

    def uwsgi_port(self):
        return self._get_setting('uwsgi_port')
