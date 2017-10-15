
from GUM_Dispenser.GUM_Exceptions import PackageNotFoundError, SourceModuleNotFoundError

import re

import ast

from tokenize import tokenize

import os

import token

from io import BytesIO

from pathlib import Path

import glob

import logging


def describe_project(distro_defs: dict, dev_directory: 'Path') -> dict:
    """Process a source project having either its packages or modules specified"""

    # At this point, we have at least a package name or module name
    # And we know that dev_directory is an existing directory

    # If we have packages and explicit modules specified by setup.py, use packages

    if 'package_names' in distro_defs:

        uml_data = {'packages' : {}}

        for package in distro_defs['package_names']:

            uml_data = describe_package(package, dev_directory, uml_data)

    elif 'module_names' in distro_defs:
        # Perform sanity check that modules exist

        ensure_modules_exist(distro_defs['module_names'], dev_directory)

        uml_data = {'modules' : {}}

        for module_name in distro_defs['module_names']:

            uml_data = describe_module('None', module_name, dev_directory, uml_data)


    return uml_data




def describe_package(name: str, dev_directory: 'Path', uml_data: dict) -> dict:
    """Process source package with the given name"""

    logging.getLogger('GUM Dispenser').info('Starting processing for package ' + name + '...')

    uml_data['packages'][name] = {'modules' : {}}

    expected_path = dev_directory.joinpath(name)

    logging.getLogger('GUM Dispenser').debug('Expecting package at ' + str(expected_path))

    # Stop if package doesn't exist

    if not expected_path.exists() or not expected_path.is_dir():

        raise(PackageNotFoundError(name))

    # Do __init__ check first to see if included modules are defined there

    logging.getLogger('GUM Dispenser').info('Checking for __init__.py...')

    init_path = Path(str(expected_path) + '/__init__.py')

    # Get a list of all the modules we are checking

    package_modules = check_init_file(name, init_path)

    # Get required data for UML markup

    for module_name in package_modules:

        uml_data = describe_module(name, module_name, expected_path, uml_data)

    return uml_data


def ensure_modules_exist(found_modules: list, package_path: 'Path') -> None:
    """Check given modules to ensure that they all exist"""

    for current_module in found_modules:

        module_path = package_path.joinpath(current_module + '.py')

        # Check result here to make sure module exists

        try:

            with open(str(module_path), 'r') as module_file:

                logging.getLogger('GUM Dispenser').info('Successfully opened ' + current_module)

        except FileNotFoundError:

            raise SourceModuleNotFoundError('The module named ' + current_module + ', specified in __init__.py, ' +
                                            'does not exist')

    logging.getLogger('GUM Dispenser').info('All specified modules exist')


def check_init_file(name : str, init_path : 'Path') -> list:
    """Attempt to find __all__ in __init__.py for given package"""

    # Read __init__ if it exists

    package_modules = []

    try:

        # Check for __all__ global variable assignments

        pattern = re.compile(r"""(?:^__all__\s*=\s*)(\[[^\[\]]*\]$)""", re.MULTILINE)

        with open(str(init_path), 'r') as init_file:

            logging.getLogger('GUM Dispenser').info('Found __init__.py')

            init_contents = init_file.read()

            # Grab the capturing group

            init_results = [current_match.group(1).strip() for current_match in pattern.finditer(init_contents)
                            if not current_match.group(1) is None and
                            not (current_match.group(1).isspace() or current_match.group(1) == '')]

            logging.getLogger('GUM Dispenser').debug(init_results)

            if len(init_results) > 0:

                logging.getLogger('GUM Dispenser').info('Found __all__ declaration. Using ' +
                                                        str(init_results[-1]) + ' as module list')

                package_modules = ast.literal_eval(init_results[-1])


                # Make sure specified modules exist before we go further

                ensure_modules_exist(package_modules, init_path.parent)

            else:

                logging.getLogger('GUM Dispenser').warning('__init__.py __all__ definition was not found for package ' +
                                                           name + '. Treating all same level .py files' +
                                                                  ' as included modules...')

    # Safely handle case where __init__ does not exist
    except FileNotFoundError:

        logging.getLogger('GUM Dispenser').warning('__init__.py does not exist for package ' + name +
                                                   '. Treating all same level .py files as included modules...')

    if len(package_modules) == 0:

        # Grab all .py files in package directory

        src_dir = init_path.parent

        logging.getLogger('GUM Dispenser').debug('Parent directory: ' + str(src_dir))

        os.chdir(src_dir)

        package_modules = glob.glob('*.py')

        package_modules = [name.rstrip('.py') for name in package_modules]


    return package_modules


# Requires dev_dir path, module name, current_data_dict

def describe_module(current_package : str, current_module : str, package_path : 'Path', current_data_dict : dict):
    """Get all information we need from a module in order to represent it in NOMNOML
    This includes all function and class declarations, properly nested and
    external package dependencies and internal module dependencies
    i.e. If a dependency is in the same package, store the module name. Otherwise, store the package name"""

    module_path = package_path.joinpath(current_module + '.py')

    # Construct our output appropriately for if we are in a package or simply checking a set of modules

    if current_package != 'None':

        # Initialize data for current module
        current_data_dict['packages'][current_package]['modules'][current_module] = {}

        module_data = current_data_dict['packages'][current_package]['modules'][current_module]

    else:

        current_data_dict['modules'][current_module] = {}

        module_data = current_data_dict['modules'][current_module]

    # Grab file text

    module_data['dependencies'] = []
    module_data['declarations'] = []

    setup_size = os.stat(str(module_path)).st_size

    logging.getLogger('GUM Dispenser').info('Reading ' + str(setup_size) + ' bytes from module ' + current_module)

    # We have already checked that the module exists
    # So proceed with the read as normal

    with open(str(module_path), 'r') as module_file:

        module_text = module_file.read(setup_size)

    # Tokenize is a generator, so we must iterate line by line over the text to get the tokenized version
    tokens = tokenize(BytesIO(module_text.encode('utf-8')).readline)

    # Split the line by whitespace, punctuation, 'from' and 'import'

    split_import_statement = re.compile(r'''(\s|[.,]|from|import)+''')

    # Catch import aliases

    import_aliases = []

    # Store scope of current token
    scope_tree = {}

    # Track scope level

    current_scope_level = scope_tree

    # Change number for every indent

    nesting_level = 0

    # Store named parent scopes that we care about: functions and classes

    parent_scope = current_module

    # Keep backward references for when we exit inner scope levels

    parent_dict = {current_module : {'dict': scope_tree, 'parent' : current_module}}

    # Store if we are reading a multi-line declaration

    multiline_declaration = False

    multiline_declaration_string = ''


    # Read tokens from every line

    for token_type, token_str, start, end, line_text in tokens:

        token_name = token.tok_name[token_type]

        logging.getLogger('GUM Dispenser').debug(str(start) + ',' + str(end) + ':\t' + token_name +
                                                 '\t' + ' (' + line_text.strip() + ')')

        # Ignore comments

        if token_name != 'COMMENT':

            if multiline_declaration:

                # If a DEDENT happens on a declaration line
                # The DEDENT will be the first token, before def or class

                # Check in case we have multiple dedents before a multiline declaration

                if token_name == 'DEDENT':

                    logging.getLogger('GUM Dispenser').debug('Found DEDENT token before ' + line_text)

                    logging.getLogger('GUM Dispenser').debug('Current tree before DEDENT: ' + str(scope_tree))

                    logging.getLogger('GUM Dispenser').debug('Exiting scope: ' + parent_scope)

                    # Exit our previous scope and put this new declaration under its parent
                    # IOW, new scope will be a sibling to previous scope

                    parent_scope = parent_dict[parent_scope]['parent']

                    current_scope_level = parent_dict[parent_scope]['dict']

                    nesting_level -= 1

                    logging.getLogger('GUM Dispenser').debug('Decremented nesting level: ' + str(nesting_level))

                # End of multiline statements have the token type NEWLINE

                if token_name == 'NEWLINE':

                    signature = multiline_declaration_string.strip().rstrip(':')

                    # Do not store duplicates
                    # We should only enter this block once per multiline declaration

                    # Log the name of the function/class we just added

                    logging.getLogger('GUM Dispenser').info('Finished multiline declaration')

                    # Store the declaration

                    module_data['declarations'].append(signature)

                    logging.getLogger('GUM Dispenser').debug('Inserted multiline declaration: \n' + signature)

                    # Store current parent and scope level for future

                    parent_dict[signature] = {'parent': parent_scope,
                                              'dict': current_scope_level}

                    # Make this function/class the parent until we exit its scope

                    parent_scope = signature

                    # Enter the scope of this new function/class

                    current_scope_level[signature] = {'current_scope_name': token_str}

                    current_scope_level = current_scope_level[parent_scope]

                    multiline_declaration_string = ''

                    multiline_declaration = False

                # Line breaks which are continuations in the same statement have the token type NL
                # Remove these linebreaks so we can format the declaration ourselves later

                elif token_name != 'NL':

                    if line_text.strip() not in multiline_declaration_string:

                        multiline_declaration_string += ' ' + line_text.strip()



            # Catch the import lines for functions and classes
            # Avoid comment lines

            elif token_name != 'STRING' and ('import ' == line_text.strip()[:7] or
                                             (' import ' in line_text.lower() and line_text.strip()[0] != '#')):

                # Import statements should not contain string literals
                # Ignore if this line of code is printing keywords as literals e.g. 'import ......'

                if "'" not in line_text and '"' not in line_text:

                    # Remove punctuation, whitespace, 'from' and 'import'

                    import_keywords = [import_name for import_name in split_import_statement.split(line_text.strip())
                                       if not import_name.isspace() and import_name != '' and import_name != '.']

                    # If an alias is used in a subsequent import, it would logically be the first keyword in the line
                    # No sense in making an alias if you are still referencing it with its parent...

                    # Update: removing condition 'if import_keywords[0] not in import_aliases'
                    # Python import aliasing makes an alias for the module object, not an import path
                    # This means that aliases cannot be referenced in subsequent import statements as parents
                    # Reference: https://stackoverflow.com/questions/42459939/import-modules-using-an-alias

                    # External dependency
                    # We want to store the package dependency

                    if current_package not in import_keywords:

                        logging.getLogger('GUM Dispenser').debug('External dependency line: ' + str(import_keywords))

                        dependency = import_keywords[0]


                    # The dependency is defined in our current source package

                    else:

                        logging.getLogger('GUM Dispenser').debug('Internal dependency line: ' + str(import_keywords))

                        dependency = import_keywords[1]


                    # Do not store duplicate dependencies

                    if dependency not in module_data['dependencies']:

                        module_data['dependencies'].append(dependency)

                        if len(import_keywords) > 2 and import_keywords[-2] == 'as':

                            if import_keywords[-1] not in import_aliases:

                                import_aliases.append(import_keywords[-1])

                            else:

                                logging.getLogger('GUM Dispenser').error('You used the same import alias twice ' +
                                                                         'for two different imports...')


            # Catch if we are at a function or class declaration

            elif line_text.strip()[:4] == 'def ' or line_text.strip()[:6] == 'class ':

                # If a DEDENT happens on a declaration line
                # The DEDENT will be the first token, before def or class

                if token_name == 'DEDENT':

                    logging.getLogger('GUM Dispenser').debug('Found DEDENT token before ' + line_text)

                    logging.getLogger('GUM Dispenser').debug('Current tree before DEDENT: ' + str(scope_tree))

                    logging.getLogger('GUM Dispenser').debug('Exiting scope: ' + parent_scope)

                    # Exit our previous scope and put this new declaration under its parent
                    # IOW, new scope will be a sibling to previous scope

                    parent_scope = parent_dict[parent_scope]['parent']

                    current_scope_level = parent_dict[parent_scope]['dict']

                    nesting_level -= 1

                    logging.getLogger('GUM Dispenser').debug('Decremented nesting level: ' + str(nesting_level))

                # Handle multiline declarations

                if line_text.strip()[-1] != ':':

                    multiline_declaration_string += line_text.strip()

                    multiline_declaration = True

                # Store the declaration when we hit the function/class name
                # This is the first 'NAME' token after def or class

                elif token_name == 'NAME' and token_str != 'def' and token_str != 'class':

                    # Store the full declaration line

                    signature = line_text.strip().rstrip(':')

                    # Do not store duplicates
                    # We should only enter this block once per unique declaration

                    if signature not in module_data['declarations']:

                        # Log the name of the function/class we just added

                        logging.getLogger('GUM Dispenser').info('Caught declaration for ' + token_str)

                        # Store the declaration

                        module_data['declarations'].append(signature)

                        # Store current parent and scope level for future

                        parent_dict[signature] = {'parent' : parent_scope,
                                                  'dict' : current_scope_level}

                        # Make this function/class the parent until we exit its scope

                        parent_scope = signature

                        # Enter the scope of this new function/class

                        current_scope_level[signature] = {'current_scope_name' : token_str}

                        current_scope_level = current_scope_level[parent_scope]





            # If a dedent happens outside of a function/class declaration
            # We need to record the level change, as this will affect the number of subsequent INDENT/DEDENTS
            # But we do not change the named scope we are in

            elif token_name == 'DEDENT':

                nesting_level -= 1

                logging.getLogger('GUM Dispenser').debug('Decremented nesting level: ' + str(nesting_level) +
                                                         ' at line ' + line_text)


            # INDENTs always occur after we will have recorded our named scope
            # So we can increment level without touching our named scope storage

            if token_name == 'INDENT':

                nesting_level += 1

                logging.getLogger('GUM Dispenser').debug('Incremented nesting level: ' + str(nesting_level) +
                                                         ' at line ' + line_text)

    # Use our correctly leveled dictionary that shows nesting instead of a list of declarations

    module_data['declarations'] = scope_tree

    logging.getLogger('GUM Dispenser').debug('Dictionary data after processing ' + current_module +
                                             ': ' + str(current_data_dict))

    return current_data_dict



