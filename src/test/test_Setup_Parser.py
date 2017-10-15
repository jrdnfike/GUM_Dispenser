
import unittest

from unittest.mock import Mock, patch

from pathlib import Path

import sys

import os

from GUM_Dispenser.GUM_setup_parser import parse_setup, read_setup_contents, check_setup_size, handle_invalid_setup_size

from GUM_Dispenser.GUM_Dispenser_Main import initialize_log

from GUM_Dispenser.GUM_Exceptions import UserConfirmedInvalidSetup, ConfigurationNotFoundError


# Mock for setup size > 2 KB
class MockSize:

    st_size = 2500


# Mock for test parsing setup.py with module definitions
def mock_read_module_defs(setup_path: str, setup_specs: dict) -> dict:

    return {'module_names': '[\'GUM_Dispenser\']'}


# Mock for test parsing setup.py without package or module definitions
def mock_read_no_defs(setup_path: str, setup_specs: dict) -> dict:

    return {}


def setUpModule():

    initialize_log({'debug': False})


class TestSetupParser(unittest.TestCase):

    def setUp(self):

        self.base_src_dir = Path(sys.modules[__name__].__file__)

        self.base_src_dir = self.base_src_dir.resolve().parent.parent

    def test_check_setup_size(self):
        """Test GUM_Dispenser.GUM_setup_parser.check_setup_size"""

        # setup.py for GUM_Dispenser < 2 KB

        with self.assertLogs(logger='GUM Dispenser', level='INFO') as log_context:

            setup_specs = check_setup_size(str(self.base_src_dir))

        self.assertTrue('Found setup.py' in log_context.output[0])

        self.assertTrue(setup_specs['valid_size'])


        # Mock so we get a setup size > 2 KB

        mock_get_setup_size = Mock(return_value=MockSize)


        with patch('os.stat', new=mock_get_setup_size):

            setup_specs = check_setup_size(str(self.base_src_dir))

        self.assertFalse(setup_specs['valid_size'])


    def test_handle_invalid_setup_size(self):
        """Test GUM_Dispenser.GUM_setup_parser.handle_invalid_setup"""

        # Test user continuing after prompt

        mock_prompt = Mock(side_effect=lambda text: 'yes')

        with patch('builtins.input', new=mock_prompt):

            handle_invalid_setup_size(str(self.base_src_dir))



        # Test user stopping after prompt

        mock_prompt = Mock(side_effect=lambda text: 'no')

        with patch('builtins.input', new=mock_prompt):

            self.assertRaises(UserConfirmedInvalidSetup, handle_invalid_setup_size, str(self.base_src_dir))


    def test_parse_setup(self):
        """Test GUM_Dispenser.GUM_setup_parser.parse_setup"""

        # Test error is still raised from parse_setup if size is > 2 KB

        mock_check_setup = Mock(side_effect=lambda setup_path: {'valid_size' : False})

        mock_prompt = Mock(side_effect=lambda text: 'no')

        with patch('GUM_Dispenser.GUM_setup_parser.check_setup_size', new=mock_check_setup):

            with patch('builtins.input', new=mock_prompt):

                self.assertRaises(UserConfirmedInvalidSetup, parse_setup, str(self.base_src_dir))


        # Test normal execution of setup parser
        # We should have the 'GUM_Dispenser' package identified

        setup_info = parse_setup(str(self.base_src_dir))

        self.assertEqual(setup_info['package_names'], ['GUM_Dispenser'])


        # Test handling missing entry point and module definition instead of package

        with patch('GUM_Dispenser.GUM_setup_parser.read_setup_contents', new=mock_read_module_defs):

            with self.assertLogs(logger='GUM Dispenser', level='WARNING') as log_context:

                parse_setup(str(self.base_src_dir))

            self.assertTrue('You do not have an entry point set for your package in setup.py.\n' in log_context.output[0])


        # Test handling missing package and modules

        with patch('GUM_Dispenser.GUM_setup_parser.read_setup_contents', new=mock_read_no_defs):

            self.assertRaises(ConfigurationNotFoundError, parse_setup, str(self.base_src_dir))


if __name__ == '__main__':

    unittest.main()

