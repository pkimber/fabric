import os

from fabric.api import (
    abort,
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

env.use_ssh_config = True


@task
def drupal(site_name, archive):
    """
    fab -H web@drop-temp -f lamp.py drupal:site_name=hatherleigh_net,archive=drupal-6.29.tar.gz
    """
    print(green("install drupal:\n{}".format(archive)))
    local_download = os.path.join(
        os.path.expanduser('~'),
        'Downloads',
        'drupal',
        archive,
    )
    if not os.path.exists(local_download):
        abort(
            "local copy of drupal archive does not exist.\n{}\n"
            "Please download a copy...".format(local_download)
        )
    temp = os.path.join(
        '/',
        'home',
        'web',
        'repo',
        'temp',
    )
    remote_download = os.path.join(temp, archive)
    if not exists(remote_download):
        put(
            local_download,
            remote_download,
        )
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
        run('tar --strip-components=1 -xzf {}'.format(os.path.join(temp, archive)))
    print(green("complete"))
