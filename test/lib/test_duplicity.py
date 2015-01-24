# -*- encoding: utf-8 -*-
import os

from lib.duplicity import Duplicity
from test.lib.helper import get_site_info


def test_find_sql():
    module_folder = os.path.dirname(os.path.realpath(__file__))
    restore_to = os.path.join(module_folder, 'data', 'duplicity', 'restore_to')
    duplicity = Duplicity(get_site_info(), 'backup')
    assert '20150124_0100.sql' in duplicity._find_sql(restore_to)
