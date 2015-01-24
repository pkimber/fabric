# -*- encoding: utf-8 -*-
import os

from lib.site.info import SiteInfo


def get_test_cert_folder(folder_name):
    module_folder = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(module_folder, 'site', folder_name)


def get_test_data_folder(folder_name):
    module_folder = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(module_folder, 'site', folder_name)


def get_site_info():
    """This is a valid 'SiteInfo' object."""
    return SiteInfo(
        'drop-temp',
        'csw_web',
        get_test_data_folder('data'),
        get_test_cert_folder('cert'),
    )
