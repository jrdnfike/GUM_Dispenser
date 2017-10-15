

from GUM_Dispenser.GUM_Generate_NOMNOML import generate_project_nomnoml, generate_module_nomnoml

from GUM_Dispenser.GUM_Dispenser_Main import initialize_log

import unittest

def setUpModule():

    initialize_log({'debug' : False})

class TestGUMGenerateNOMNOML(unittest.TestCase):

    def test_generate_project_nomnoml(self):
        """Test NOMNOML Generation"""

        # Test with our current source code dictionary (or a dictionary close to it)

        test_uml_data = {'packages':
                             {'GUM_Dispenser':
                                  {'modules':
                                       {'GUM_Dispenser_Main':
                                            {'dependencies':
                                                 ['pathlib', 'GUM_Exceptions', 'GUM_setup_parser',
                                                  'GUM_Describe_Source'],
                                             'declarations': {"def define_arguments() -> 'ArgumentParser'": {
                                                 'current_scope_name': 'define_arguments'},
                                                 'def initialize_log() -> None': {
                                                     'current_scope_name': 'initialize_log'},
                                                 'def check_for_setup(arguments_received: dict) -> str':
                                                     {'current_scope_name': 'check_for_setup'},
                                                 'def dispense_gum(arguments_received: dict) -> None':
                                                     {'current_scope_name': 'dispense_gum'},
                                                 'def main()': {'current_scope_name': 'main'}}},
                                        'GUM_setup_parser': {'dependencies': ['GUM_Exceptions', 'pathlib'],
                                                             'declarations': {
                                                                 'def check_setup_size(setup_path : str) -> dict':
                                                                     {'current_scope_name': 'check_setup_size'},
                                                                 'def handle_invalid_setup_size(setup_path : str) -> None':
                                                                     {'current_scope_name':
                                                                          'handle_invalid_setup_size'},
                                                                 'def read_setup_contents(setup_path: str, setup_specs: dict) -> dict': {
                                                                     'current_scope_name': 'read_setup_contents'},
                                                                 'def parse_setup(setup_path: str) -> dict': {
                                                                     'current_scope_name': 'parse_setup'}}},
                                        'GUM_Describe_Source': {'dependencies':
                                                                    ['GUM_Exceptions', 'tokenize', 'io', 'pathlib'],
                                                                'declarations': {
                                                                    "def describe_project(distro_defs: dict, dev_directory: 'Path') -> dict":
                                                                        {'current_scope_name': 'describe_project'},
                                                                    "def describe_package(name: str, dev_directory: 'Path', uml_data: dict) -> dict":
                                                                        {'current_scope_name': 'describe_package'},
                                                                    "def ensure_modules_exist(found_modules: list, package_path: 'Path') -> None":
                                                                        {'current_scope_name': 'ensure_modules_exist'},
                                                                    "def check_init_file(name : str, init_path : 'Path') -> list":
                                                                        {'current_scope_name': 'check_init_file'},
                                                                    "def describe_module(current_package : str, current_module : str, package_path : 'Path', current_data_dict : dict)":
                                                                        {'current_scope_name': 'describe_module'}}},
                                        'GUM_Generate_NOMNOML': {'dependencies': [],
                                                                 'declarations': {
                                                                     'def generate_package_nomnoml(source_data: dict, entry_points: list) -> str':
                                                                         {'current_scope_name': 'generate_package_nomnoml'},
                                                                     'def generate_module_nomnoml(module_data: dict, entry_points: list, current_package: str, current_module: str) -> str':
                                                                         {'current_scope_name': 'generate_module_nomnoml'},
                                                                     'def process_declaration(declaration_data: dict, declaration: str, entry_points: list, current_package: str,':
                                                                         {'current_scope_name': 'process_declaration'},
                                                                     'def beautify_declaration_markup(markup: str) -> str': {
                                                                         'current_scope_name': 'beautify_declaration_markup'}}},
                                        'GUM_Exceptions': {'dependencies': [],
                                                           'declarations': {
                                                               'class InvalidSourcePathError(Exception)': {
                                                                   'current_scope_name': 'InvalidSourcePathError'},
                                                               'class ConfigurationNotFoundError(Exception)': {
                                                                   'current_scope_name': 'ConfigurationNotFoundError'},
                                                               'class PackageNotFoundError(Exception)': {
                                                                   'current_scope_name': 'PackageNotFoundError'},
                                                               'class SourceModuleNotFoundError(Exception)':
                                                                   {'current_scope_name': 'SourceModuleNotFoundError'},
                                                               'class UserConfirmedInvalidSetup(Exception)': {
                                                                   'current_scope_name': 'UserConfirmedInvalidSetup'}}}
                                        }
                                   }
                              }
                         }


        sample_nomnoml = generate_project_nomnoml(test_uml_data, ['GUM_Dispenser.GUM_Dispenser_Main:main'])

        # Try pasting the results into nomnoml.com!!

        self.assertTrue('<entry>def main()' in sample_nomnoml)

        # Test with module data only, a module without declarations, and a module with nested declarations

        test_uml_data = {'modules' :
                         {'no_declarations' : {'dependencies' : ['nested_declaration'],
                                               'declarations' : {}},
                          'nested_declaration' : {'dependencies' : [],
                                                  'declarations': {
                                                         'def outer() -> None': {
                                                             'current_scope_name' : 'outer',
                                                             'def inner() -> None' : {'current_scope_name' : 'inner'}
                                                         }
                                                  }
                                                  }
                          }
                         }

        sample_nomnoml = generate_project_nomnoml(test_uml_data, ['nested_declaration:outer', 'no_declarations'])

        self.assertTrue('<entry>def outer()' in sample_nomnoml)

        self.assertTrue('<entry>no_declarations' in sample_nomnoml)


if __name__ == '__main__':

    unittest.main()

