"""Find the server name from the pillar folder."""

import os
import yaml

from lib.error import TaskError
from lib.site.info import SiteInfo


def _get_server_name(pillar_folder, site_name, testing):
    result = None
    with open(os.path.join(pillar_folder, 'top.sls'), 'r') as f:
        data = yaml.load(f.read())
        base = data.get('base')
        for k, v in base.iteritems():

            info = SiteInfo(k, site_name, pillar_folder)
            if testing == info.is_testing:
                result = k
    if not result:
        status = 'testing' if testing else 'live'
        raise TaskError(
            "cannot find server name for site '{}' ({}) "
            "in pillar {}".format(site_name, status, pillar_folder)
        )
    if '*' in result:
        raise TaskError(
            "'{}' does not appear to be a valid host name".format(result)
        )
    return result


def get_server_name_live(pillar_folder, site_name):
    return _get_server_name(pillar_folder, site_name, testing=False)


def get_server_name_testing(pillar_folder, site_name):
    return _get_server_name(pillar_folder, site_name, testing=True)
