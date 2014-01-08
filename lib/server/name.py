"""Find the server name from the pillar folder."""

import os
import yaml


def get_server_name(pillar_folder, site_name):
    found_sites = False
    result = None
    with open(os.path.join(pillar_folder, 'top.sls'), 'r') as f:
        data = yaml.load(f.read())
        base = data.get('base')
        for k, v in base.iteritems():
            for name in v:
                names = name.split('.')
                file_name = os.path.join(pillar_folder, *names)
                file_name = file_name + '.sls'
                with open(file_name, 'r') as fa:
                    attr = yaml.load(fa.read())
                    if len(attr) > 1:
                        raise ServerNameError(
                            "Unexpected state: 'sls' file contains more "
                            "than one key: {}".format(file_name)
                        )
                    key = attr.iterkeys().next()
                    if key == 'sites':
                        found_sites = True
                        sites = attr[key]
                        for name, settings in sites.iteritems():
                            if name == site_name:
                                if result:
                                    raise ServerNameError(
                                        "found site '{}' on more than "
                                        "one server in the pillar: '{}' "
                                        "and '{}'".format(
                                            site_name, result, k
                                        )
                                    )
                                result = k
    if not found_sites:
        raise ServerNameError(
            "Cannot find 'sites' key in the pillar: '{}'".format(
                pillar_folder
            )
        )
    if not result:
        raise ServerNameError(
            "cannot find server name for site '{}'".format(site_name)
        )
    if '*' in result:
        raise ServerNameError(
            "'{}' does not appear to be a valid host name".format(result)
        )
    return result
