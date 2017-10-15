
import unittest

from unittest.mock import patch, Mock, DEFAULT

from GUM_Dispenser.GUM_Dispenser_Main import check_for_setup, dispense_gum, main, initialize_log

from pathlib import Path

from GUM_Dispenser.GUM_Exceptions import ConfigurationNotFoundError, PackageNotFoundError, SourceModuleNotFoundError

from GUM_Dispenser.GUM_Exceptions import UserConfirmedInvalidSetup

import sys


class TestGumDispenserMain(unittest.TestCase):

    def setUp(self):

        self.base_pkg_dir = Path(sys.modules[__name__].__file__)

        self.base_pkg_dir = self.base_pkg_dir.resolve().parent.parent


    def test_initialize_log(self):

        test_arguments = {'debug' : True}

        with self.assertLogs('GUM Dispenser', level='INFO') as log_context:

            initialize_log(test_arguments)

        self.assertTrue('DEBUG' in log_context.output[1])


        test_arguments = {'debug': False}


        with self.assertLogs('GUM Dispenser', level='INFO') as log_context:
            initialize_log(test_arguments)

        self.assertTrue('INFO' in log_context.output[1])



    def test_check_for_setup(self):
        """Test GUM_Dispenser.GUM_Dispenser.check_for_setup"""

        # Test non-existent setup file and input as base directory

        test_arguments = {'setup_file' : 'nonexistent', 'path' : str(self.base_pkg_dir), 'debug' : False}

        self.assertEqual(str(self.base_pkg_dir), check_for_setup(test_arguments))


        # Test non-existent setup file and input as package directory

        test_arguments['path'] = str(self.base_pkg_dir.joinpath('GUM_Dispenser'))

        self.assertEqual(str(self.base_pkg_dir), check_for_setup(test_arguments))



        # Test with given directory containing setup

        test_arguments['setup_file'] = str(self.base_pkg_dir)

        self.assertEqual(str(self.base_pkg_dir), check_for_setup(test_arguments))


        # Test with direct path to setup.py given

        test_arguments['setup_file'] = str(self.base_pkg_dir.joinpath('setup.py'))

        self.assertEqual(str(self.base_pkg_dir), check_for_setup(test_arguments))



        # Test where no setup.py will be found

        test_arguments['setup_file'] = 'nonexistent'
        test_arguments['path'] = str(self.base_pkg_dir.parent)

        self.assertRaises(ConfigurationNotFoundError, check_for_setup, test_arguments)



    def test_dispense_gum(self):
        """Test GUM_Dispenser.GUM_Dispenser.dispense_gum"""

        # Test error handling
        # Here is InvalidSourcePathError

        test_arguments = {'path' : 'nonexistent', 'debug' : False}

        with self.assertLogs(logger='GUM Dispenser', level='ERROR') as log_context:

            dispense_gum(test_arguments)

        self.assertTrue("The given source path was not found on your system" in log_context.output[0])


        test_arguments = {'path' : self.base_pkg_dir}


        with patch('GUM_Dispenser.GUM_Dispenser_Main.check_for_setup', new=Mock(side_effect=ConfigurationNotFoundError)):

            with self.assertLogs(logger='GUM Dispenser', level='ERROR') as log_context:

                dispense_gum(test_arguments)

            self.assertTrue("We couldn't find a complete project definition" in log_context.output[0])


        with patch('GUM_Dispenser.GUM_Dispenser_Main.check_for_setup', new=Mock(side_effect=PackageNotFoundError(
                'nonexistent'))):

            with self.assertLogs(logger='GUM Dispenser', level='ERROR') as log_context:

                dispense_gum(test_arguments)

            self.assertTrue("The package nonexistent specified in your setup.py doesn't exist" in log_context.output[0])


        with patch('GUM_Dispenser.GUM_Dispenser_Main.check_for_setup', new=Mock(side_effect=SourceModuleNotFoundError)):

            with self.assertLogs(logger='GUM Dispenser', level='ERROR') as log_context:

                dispense_gum(test_arguments)

            self.assertTrue("Missing or bad path for .py source file" in log_context.output[0])


        with patch('GUM_Dispenser.GUM_Dispenser_Main.check_for_setup', new=Mock(side_effect=UserConfirmedInvalidSetup)):

            with self.assertLogs(logger='GUM Dispenser', level='ERROR') as log_context:

                dispense_gum(test_arguments)

            self.assertTrue("User requested program termination. Goodbye" in log_context.output[0])


        with patch('GUM_Dispenser.GUM_Dispenser_Main.check_for_setup', new=Mock(side_effect=KeyError)):

            with self.assertLogs(logger='GUM Dispenser', level='ERROR') as log_context:

                dispense_gum(test_arguments)

            self.assertTrue("Error:" in log_context.output[0])


        # Test that already checked functions are called as expected

        with patch.multiple('GUM_Dispenser.GUM_Dispenser_Main', check_for_setup=DEFAULT, parse_setup=DEFAULT,
                            describe_project=DEFAULT, generate_project_nomnoml=DEFAULT) as patched:

            dispense_gum(test_arguments)

            patched['check_for_setup'].assert_called_once()

            patched['parse_setup'].assert_called_once()

            patched['describe_project'].assert_called_once()

            patched['generate_project_nomnoml'].assert_called_once()



    def test_main(self):
        """Test GUM_Dispenser.GUM_Dispenser.main"""

        with patch.multiple('GUM_Dispenser.GUM_Dispenser_Main', argparse=DEFAULT, dispense_gum=DEFAULT,
                            initialize_log=DEFAULT) as patched:

            main()

            patched['dispense_gum'].assert_called_once()






if __name__ == '__main__':

    unittest.main()