import getpass
import os

from datetime import datetime

from lib.error import TaskError
from lib.site.info import SSL_CERT_NAME
from lib.site.info import SSL_SERVER_KEY


class FolderInfo(object):
    """
    Standard folder names for deploying projects and for running fabric
    commands
    """

    def __init__(self, site_info, version=None):
        self.site_info = site_info
        if version:
            self.date_folder = self._get_date_folder(version)
        else:
            self.date_folder = None

    def _get_date_folder(self, version):
        return '{}__{}_{}'.format(
            version.replace('.', '_'),
            datetime.now().strftime('%Y%m%d_%H%M%S'),
            getpass.getuser()
        )

    def _repo(self):
        return '/home/web/repo'

    def deploy(self):
        return os.path.join(self.site(), 'deploy')

    def install(self):
        if not self.date_folder:
            raise TaskError(
                "Cannot return an install folder if the class wasn't "
                "constructed with a version number e.g. '0.2.32'"
            )
        return os.path.join(self.deploy(), self.date_folder)

    def install_temp(self):
        return os.path.join(self.install(), 'temp')

    def install_venv(self):
        return os.path.join(self.install(), 'venv')

    def live(self):
        return os.path.join(self.site(), 'live')

    def live_venv(self):
        return os.path.join(self.live(), 'venv')

    def site(self):
        return os.path.join(
            self._repo(),
            'project',
            self.site_info.site_name,
        )

    def ssl_cert(self):
        return os.path.join(self.ssl_cert_folder(), SSL_CERT_NAME)

    def ssl_server_key(self):
        return os.path.join(self.ssl_cert_folder(), SSL_SERVER_KEY)

    def ssl_cert_folder(self):
        return os.path.join(self.ssl_folder(), self.site_info.domain)

    def ssl_folder(self):
        return os.path.join(self.srv_folder(), 'ssl')

    def srv_folder(self):
        return os.path.join('/', 'srv')

    def upload(self):
        """upload archive files using rsync (drupal etc)"""
        return os.path.join(self._repo(), 'upload')

    def vassal(self):
        return os.path.join(
            self._repo(),
            'uwsgi',
            'vassals',
            '{}.ini'.format(self.site_info.site_name)
        )
