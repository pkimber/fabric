import os

from fabric.api import cd
from fabric.api import run
from fabric.colors import yellow
from fabric.context_managers import shell_env


class DjangoCommand(object):

    def __init__(self, site_folder, venv_folder, site_info):
        self.site_folder = site_folder
        self.venv_folder = venv_folder
        self.site_info = site_info

    def _run_command(self, command):
        param = dict(
            command=command,
            manage=os.path.join(self.site_folder, 'manage.py'),
            venv=os.path.join(self.venv_folder, 'bin', 'python'),
        )
        with cd(self.site_folder), shell_env(**self.site_info.env()):
            run('{venv} {manage} {command}'.format(**param))

    def collect_static(self):
        self._run_command('collectstatic --noinput')

    def compress(self):
        if self.site_info.is_amazon:
            self._run_command('compress')

    def haystack_index_clear(self):
        self._run_command('clear_index --noinput')

    def haystack_index(self):
        self._run_command('update_index')

    def init_project(self):
        self._run_command('init_project')

    def migrate_database(self):
        """
        Run South database migrations.

        Note: South will not work on a new empty database until the initial Django
        and South tables are created using the following command:

        python manage.py syncdb --noinput
        """
        self._run_command('migrate --all --noinput')

    def syncdb(self):
        self._run_command('syncdb --noinput')
