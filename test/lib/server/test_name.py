import os
import unittest

from lib.dev.folder import get_pillar_folder
from lib.error import TaskError
from lib.server.name import get_server_name


class TestName(unittest.TestCase):

    def test_name(self):
        module_folder = os.path.dirname(os.path.realpath(__file__))
        folder = os.path.join(module_folder, '..', 'site', 'data')
        folder = os.path.abspath(folder)
        self.assertEqual(
            'drop-temp',
            get_server_name(get_pillar_folder(folder), 'csw_web')
        )
