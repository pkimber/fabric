"""Find the server name from the pillar folder."""

import os
import yaml

from lib.error import (
    SiteNotFoundError,
    TaskError,
)
from lib.siteinfo import SiteInfo


def get_server_name(pillar_folder, domain):
    result = None
    with open(os.path.join(pillar_folder, 'top.sls'), 'r') as f:
        data = yaml.load(f.read())
        base = data.get('base')
        for k, v in base.items():
            if '*' in k:
                pass
            else:
                try:
                    info = SiteInfo(k, domain, pillar_folder)
                    result = k
                except SiteNotFoundError:
                    pass
    if not result:
        raise TaskError(
            "cannot find '{}' in pillar '{}'.".format(domain, pillar_folder)
        )
    if '*' in result:
        raise TaskError(
            "'{}' does not appear to be a valid host name".format(result)
        )
    return result
