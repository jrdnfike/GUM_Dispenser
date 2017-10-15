
import unittest

from unittest.mock import patch

from pathlib import Path

from GUM_Dispenser.GUM_Exceptions import SourceModuleNotFoundError, PackageNotFoundError

from GUM_Dispenser.GUM_Describe_Source import check_init_file, ensure_modules_exist, describe_module, describe_package

from GUM_Dispenser.GUM_Describe_Source import describe_project

from GUM_Dispenser.GUM_Dispenser_Main import initialize_log

import sys


def setUpModule():

    initialize_log({'debug' : False})


class TestGUMDescribeSource(unittest.TestCase):

    def setUp(self):

        self.base_pkg_dir = Path(sys.modules[__name__].__file__)

        self.base_pkg_dir = self.base_pkg_dir.resolve().parent.parent.joinpath('GUM_Dispenser')


    def test_ensure_modules_exist(self):
        """Test GUM_Dispenser.GUM_Describe_Source.ensure_modules_exist"""

        # Test when a module doesn't exist

        self.assertRaises(SourceModuleNotFoundError, ensure_modules_exist, ['nonexistent'], self.base_pkg_dir)


        # Test when all given modules exist

        with self.assertLogs(logger='GUM Dispenser', level='INFO') as log_context:

            ensure_modules_exist(['GUM_Dispenser_Main'], self.base_pkg_dir)

        self.assertTrue('Successfully opened GUM_Dispenser' in log_context.output[0])

        self.assertTrue('All specified modules exist' in log_context.output[1])


    def test_check_init_file(self):
        """Test GUM_Dispenser.GUM_Describe_Source.check_init_file"""

        # We don't declare __all__ in our __init__
        # Check we handle this case appropriately

        self.base_pkg_dir = self.base_pkg_dir.parent.joinpath('test').joinpath('dummy')

        with self.assertLogs(logger='GUM Dispenser', level='WARNING') as log_context:

            pkg_modules = check_init_file('dummy', self.base_pkg_dir.joinpath('__init__.py'))

        self.assertTrue('__init__.py __all__ definition was not found for package dummy' in
                        log_context.output[0])

        self.assertTrue('__init__' in pkg_modules)
        self.assertTrue('bad_imports' in pkg_modules)


        # Test we handle a non-existent __init__ appropriately

        self.base_pkg_dir = self.base_pkg_dir.parent

        with self.assertLogs(logger='GUM Dispenser', level='WARNING') as log_context:

            pkg_modules = check_init_file('test', self.base_pkg_dir.joinpath('__init__.py'))

        self.assertTrue('__init__.py does not exist for package test. Treating all same level .py files ' +
                        'as included modules...' in log_context.output[0])

        self.assertTrue(len(pkg_modules) > 0)

        self.assertTrue('test_Setup_Parser' in pkg_modules)


        # Test using current package where we do have __all__ defined

        self.base_pkg_dir = self.base_pkg_dir.parent.joinpath('GUM_Dispenser')

        with self.assertLogs(logger='GUM Dispenser', level='INFO') as log_context:

            pkg_modules = check_init_file('GUM_Dispenser', self.base_pkg_dir.joinpath('__init__.py'))

        self.assertTrue('Found __init__.py' in log_context.output[0])

        self.assertTrue('Found __all__ declaration.' in log_context.output[1])

        self.assertTrue(len(pkg_modules) > 0)

        self.assertTrue('GUM_Dispenser_Main' in pkg_modules)


    def test_describe_module(self):
        """Test GUM_Dispenser.GUM_Describe_Source.describe_module"""

        test_source_data = {'packages' : {'GUM_Dispenser' : {'modules' : {}}}}

        test_source_data = describe_module('GUM_Dispenser', 'GUM_Describe_Source', self.base_pkg_dir, test_source_data)

        module_data = test_source_data['packages']['GUM_Dispenser']['modules']['GUM_Describe_Source']

        self.assertTrue('GUM_Exceptions' in module_data['dependencies'])

        self.assertTrue('def describe_module(current_package : str, current_module : str, package_path : \'Path\', ' +
                        'current_data_dict : dict)' in module_data['declarations'])


        # Ensure functionality is preserved if not identified as part of a package

        test_source_data = {'modules': {}}

        test_source_data = describe_module('None', 'GUM_Describe_Source', self.base_pkg_dir, test_source_data)

        module_data = test_source_data['modules']['GUM_Describe_Source']


        # Now we treat GUM_Dispenser as an outside package for dependency purposes

        self.assertTrue('GUM_Dispenser' in module_data['dependencies'])

        self.assertTrue('def describe_module(current_package : str, current_module : str, package_path : \'Path\', ' +
                        'current_data_dict : dict)' in module_data['declarations'])


        # Test bad import aliasing: reusing an alias

        self.base_pkg_dir = self.base_pkg_dir.parent.joinpath('test').joinpath('dummy')

        test_source_data = {'modules' : {}}

        with self.assertLogs(logger='GUM Dispenser', level='ERROR') as log_context:

            test_source_data = describe_module('None', 'bad_imports', self.base_pkg_dir, test_source_data)

        self.assertTrue('xml' in test_source_data['modules']['bad_imports']['dependencies'])

        self.assertTrue('You used the same import alias twice for two different imports...' in log_context.output[0])




    def test_describe_package(self):
        """Test GUM_Dispenser.GUM_Describe_Source.describe_package"""

        # Set up test data and acquire results

        test_source_data = {'packages' : {'GUM_Dispenser' : {'modules' : {}}}}

        test_source_data = describe_package('GUM_Dispenser', self.base_pkg_dir.parent, test_source_data)

        test_pkg_data = test_source_data['packages']['GUM_Dispenser']

        # Test that modules are present
        # Module data is tested with describe_module test

        self.assertTrue('GUM_Describe_Source' in test_pkg_data['modules'])

        self.assertTrue('GUM_Dispenser_Main' in test_pkg_data['modules'])

        self.assertTrue('GUM_Exceptions' in test_pkg_data['modules'])


        # Test checking for nonexistent package

        test_source_data = {'packages': {'GUM_Dispenser': {'modules': {}}}}

        self.assertRaises(PackageNotFoundError, describe_package, 'nonexistent',
                          self.base_pkg_dir.parent, test_source_data)



    def test_describe_project(self):
        """Test GUM_Dispenser.GUM_Describe_Source.describe_project"""

        # Test processing a package works correctly

        test_distro_defs = {'package_names' : ['GUM_Dispenser']}

        uml_data = describe_project(test_distro_defs, self.base_pkg_dir.parent)

        # print(uml_data)

        test_pkg_data = uml_data['packages']['GUM_Dispenser']

        self.assertTrue('GUM_Describe_Source' in test_pkg_data['modules'])

        self.assertTrue('GUM_Dispenser_Main' in test_pkg_data['modules'])

        self.assertTrue('GUM_Exceptions' in test_pkg_data['modules'])


        # Test processing a list of unpackaged modules

        test_distro_defs = {'module_names': ['GUM_Describe_Source']}

        uml_data = describe_project(test_distro_defs, self.base_pkg_dir)

        module_data = uml_data['modules']['GUM_Describe_Source']

        # Now we treat GUM_Dispenser as an outside package for dependency purposes
        # Since we have indicated that GUM_Describe_Source is not part of a package for purposes of this test

        self.assertTrue('GUM_Dispenser' in module_data['dependencies'])

        self.assertTrue('def describe_module(current_package : str, current_module : str, package_path : \'Path\', ' +
                        'current_data_dict : dict)' in module_data['declarations'])







if __name__ == '__main__':

    unittest.main()
