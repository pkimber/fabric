""" For docs, see https://github.com/pkimber/cloud_docs """
import os

from pkg_resources import safe_name

from fabric.api import (
    abort,
    cd,
    env,
    run,
)
from fabric.colors import (
    green,
    yellow,
)
from fabric.contrib.files import exists
from fabric.contrib.project import rsync_project

from lib.browser import BrowserDriver
from lib.command import DjangoCommand


env.use_ssh_config = True

SECRET_KEY = 'SECRET_KEY'


def download_package(site_name, prefix, version, temp_folder, venv_folder):
    package_name = '{}-{}=={}'.format(prefix, safe_name(site_name), version)
    print(green("download package: {}".format(package_name)))
    pip_bin = os.path.join(venv_folder, 'bin', 'pip')
    run('{} install --download={} --no-deps {}'.format(
        pip_bin, temp_folder, package_name
    ))


def extract_project_package(install_folder, temp_folder, site_name, prefix, version):
    package_archive = '{}-{}-{}.tar.gz'.format(prefix, safe_name(site_name), version)
    print(green("extract project package: {}".format(package_archive)))
    run('tar --strip-components=1 --directory={} -xzf {}'.format(
        install_folder,
        os.path.join(temp_folder, package_archive)
        ))


def install_requirements(prefix, install_folder, venv_folder):
    """ Download python packages from our package index """
    filename = os.path.join(install_folder, 'requirements/production.txt')
    print(green("requirements: {}".format(filename)))
    pip_bin = os.path.join(venv_folder, 'bin', 'pip')
    run("{} install --upgrade pip".format(pip_bin))
    run("{} install -r {}".format(pip_bin, filename))


def mkvirtualenv(venv_folder):
    print(green("mkvirtualenv: {}".format(venv_folder)))
    run('/usr/bin/virtualenv {} {}'.format(
        '--python=/usr/bin/python3',
        venv_folder,
    ))


def link_install_to_live_folder(install_folder, live_folder):
    print(green("link '{0}' folder to '{1}'".format(live_folder, install_folder)))
    if exists(live_folder):
        run('rm {0}'.format(live_folder))
    run('ln -s {0} {1}'.format(install_folder, live_folder))


def touch_vassal_ini(vassal_ini_file_names):
    print(green("touch"))
    for file_name in vassal_ini_file_names:
        if exists(file_name):
            run('touch {0}'.format(file_name))
        else:
            abort('uwsgi ini file does not exist: {0}'.format(file_name))


def run_post_deploy_test(site_name):
    browser_driver = BrowserDriver(site_name)
    browser_driver.test()
    browser_driver.test_sitemap()
    browser_driver.close()


def deploy_django(folder_info, site_info, version):
    # virtualenv
    mkvirtualenv(folder_info.install_venv())
    # download and extract main package
    download_package(
        site_info.package,
        site_info.prefix(),
        version,
        folder_info.install_temp(),
        folder_info.install_venv()
    )
    extract_project_package(
        folder_info.install(),
        folder_info.install_temp(),
        site_info.package,
        site_info.prefix(),
        version
    )
    # debug
    run('ls -l {0}'.format(folder_info.install()))
    # requirements
    install_requirements(
        site_info.prefix(),
        folder_info.install(),
        folder_info.install_venv()
    )
    command = DjangoCommand(
        folder_info.install(), folder_info.install_venv(), site_info
    )
    command.collect_static()
    command.compress()
    # migrate database and init project
    if site_info.has_database:
        command.migrate_database()
    command.init_project()


def django_post_deploy(folder_info):
    # re-start uwsgi apps
    touch_vassal_ini(folder_info.vassals())


def deploy_php(folder_info, site_info):
    rsync_project(
        local_dir='../deploy/upload/',
        remote_dir=folder_info.upload(),
    )
    packages = site_info.packages()
    for package in packages:
        name = package['name']
        archive = package['archive']
        folder = package.get('folder', None)
        tar_opt = package.get('tar', '')
        print(yellow(name))
        if folder:
            install = os.path.join(folder_info.install(), folder)
            if not exists(install):
                print(yellow('  {}'.format(install)))
                run('mkdir -p {}'.format(install))
        else:
            install = folder_info.install()
        with cd(install):
            print(yellow('  {}'.format(archive)))
            print(yellow('  {}'.format(tar_opt)))
            run('tar {} -xzf {}'.format(
                tar_opt,
                os.path.join(folder_info.upload(), archive),
            ))
