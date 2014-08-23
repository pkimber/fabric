import os
import unittest

from lib.dev.folder import get_pillar_folder
from lib.server.name import (
    get_server_name_live,
    get_server_name_testing,
)


class TestName(unittest.TestCase):

    def test_name(self):
        module_folder = os.path.dirname(os.path.realpath(__file__))
        folder = os.path.join(module_folder, '..', 'site', 'data')
        folder = os.path.abspath(folder)
        self.assertEqual(
            'drop-temp',
            get_server_name_live(get_pillar_folder(folder), 'csw_web')
        )

    def test_name_testing_not(self):
        """Test sites are added to the pillar twice."""
        module_folder = os.path.dirname(os.path.realpath(__file__))
        folder = os.path.join(module_folder, '..', 'site', 'data_testing')
        folder = os.path.abspath(folder)
        self.assertEqual(
            'drop',
            get_server_name_live(get_pillar_folder(folder), 'kb_couk')
        )

    def test_name_testing(self):
        """Test sites are added to the pillar twice."""
        module_folder = os.path.dirname(os.path.realpath(__file__))
        folder = os.path.join(module_folder, '..', 'site', 'data_testing')
        folder = os.path.abspath(folder)
        self.assertEqual(
            'drop-test',
            get_server_name_testing(get_pillar_folder(folder), 'kb_couk')
        )
