import os

from fabric.api import (
    cd,
    env,
    put,
    run,
    task,
)
from fabric.colors import (
    green,
    yellow,
)
from fabric.contrib.files import (
    exists,
)

DRUPAL = 'drupal-6.29.tar.gz'
DRUPAL_URL = 'http://ftp.drupal.org/files/projects'
env.use_ssh_config = True


@task
def drupal(site_name):
    """
    fab -H web@drop-temp -f lamp.py drupal:site_name=hatherleigh_net
    """
    print(green("install drupal:\n{}".format(DRUPAL)))
    temp = os.path.join(
        '/',
        'home',
        'web',
        'repo',
        'temp',
    )
    remote_download = os.path.join(temp, DRUPAL)
    if not exists(remote_download):
        local_download = os.path.join(
            os.path.expanduser('~'),
            'Downloads',
            'drupal',
            DRUPAL,
        )
        put(
            local_download,
            remote_download,
        )
    #if exists(drupal_download):
    #    print(yellow("remove old download:\n{}".format(drupal_download)))
    #    run("rm {}".format(drupal_download))
    #with cd(temp):
    #    run("wget '{}/{}'".format(DRUPAL_URL, DRUPAL))
    install = os.path.join(
        '/',
        'home',
        'web',
        'repo',
        'php',
        site_name,
    )
    print(yellow("install drupal to:\n{}".format(install)))
    with cd(install):
        run('tar --strip-components=1 -xzf {}'.format(os.path.join(temp, DRUPAL)))
