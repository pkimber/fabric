# -*- encoding: utf-8 -*-
import json
import os

from lib.duplicity import Duplicity
from test.lib.test_siteinfo import get_site_info


def test_find_sql():
    module_folder = os.path.dirname(os.path.realpath(__file__))
    restore_to = os.path.join(module_folder, 'data', 'duplicity', 'restore_to')
    duplicity = Duplicity(get_site_info(), 'backup')
    assert '20150124_0100.sql' in duplicity._find_sql(restore_to)


def test_from_to():
    module_folder = os.path.dirname(os.path.realpath(__file__))
    test_data_folder = os.path.join(module_folder, 'data', 'duplicity')
    restore_to_public = os.path.join(
        test_data_folder,
        'restore_to_files',
        'public',
    )
    media_folder = os.path.join(test_data_folder, 'media')
    duplicity = Duplicity(get_site_info(), 'files')
    result = duplicity._get_from_to(restore_to_public, media_folder)
    expect = [
        (
            os.path.join(restore_to_public, 'booking'),
            os.path.join(media_folder, 'booking'),
        ),
        (
            os.path.join(restore_to_public, 'compose'),
            os.path.join(media_folder, 'compose'),
        ),
    ]
    assert result == expect
