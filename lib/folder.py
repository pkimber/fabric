import getpass
import os

from datetime import datetime

from lib.error import TaskError


INFO_FOLDER = '../../module/deploy/'
SSL_CERT_NAME = 'ssl-unified.crt'
SSL_SERVER_KEY = 'server.key'


def get_certificate_folder():
    certificate_folder = os.path.join(INFO_FOLDER, 'ssl-cert')
    if not os.path.exists(certificate_folder):
        raise TaskError(
            "certificate folder does not exist in the standard location "
            "on your workstation: {}".format(certificate_folder)
        )
    return certificate_folder


def get_pillar_folder(pillar_folder=None):
    """Find the pillar folder on your local workstation."""
    if pillar_folder == None:
        pillar_folder = os.path.join(INFO_FOLDER, 'pillar')
    if not os.path.exists(pillar_folder):
        raise TaskError(
            "pillar folder does not exist in the standard location "
            "on your workstation: {}".format(pillar_folder)
        )
    return pillar_folder


def get_test_folder():
    test_folder = os.path.join(INFO_FOLDER, 'test')
    if not os.path.exists(test_folder):
        raise TaskError(
            "'test' folder does not exist in the standard location "
            "on your workstation: {}".format(test_folder)
        )
    return test_folder


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
            self.site_info.domain,
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

    def vassals(self):
        folder = os.path.join(
            self._repo(),
            'uwsgi',
            'vassals',
        )
        site_name = self.site_info.domain
        result = [os.path.join(folder, '{}.ini'.format(site_name)),]
        if self.site_info.is_celery:
            result.append(
                os.path.join(folder, '{}.celery.beat.ini'.format(site_name))
            )
            result.append(
                os.path.join(folder, '{}.celery.worker.ini'.format(site_name))
            )
        return result
