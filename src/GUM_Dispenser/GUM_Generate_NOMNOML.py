
import re

import logging


def generate_project_nomnoml(source_data: dict, entry_points: list) -> str:
    """Convert our stored source dictionary data into NOMNOML"""

    # Make an object class to color our entry points in NOMNOML

    pkg_nomnoml = '#.entry: fill=#8f8\n'

    # Handle if our code is organized with packages

    if 'packages' in source_data:

        # Process every package

        for package, package_data in source_data['packages'].items():

            # Process every module in the current package

            for module_name in package_data['modules']:

                # Generate NOMNOML from inside the module files to have entry points declared before references

                pkg_nomnoml = pkg_nomnoml + generate_module_nomnoml(package_data['modules'][module_name],
                                                                    entry_points, package, module_name)

                # Display the relationship between modules and packages

                pkg_nomnoml = pkg_nomnoml + '[' + package + ']-[' + module_name + ']\n\n'


    # Handle if we only have individual modules

    else:

        for module_name in source_data['modules']:

            pkg_nomnoml = pkg_nomnoml + generate_module_nomnoml(source_data['modules'][module_name],
                                                                entry_points, '', module_name) + '\n'



    return pkg_nomnoml


def generate_module_nomnoml(module_data: dict, entry_points: list, current_package: str, current_module: str) -> str:
    """Generate NOMNOML for a Python module
       Color entry points
       Show inter-module and external package dependencies"""

    module_nomnoml = ''

    # Catch if our module itself is an entry point i.e. meant to be run as a script

    if (current_package == '' and current_module in entry_points) or \
            current_package + ':' + current_module in entry_points:

        module_nomnoml = module_nomnoml + '[<entry>' + current_module

    # Begin non-colored block

    else:

        module_nomnoml = module_nomnoml + '[' + current_module

    # Always process declarations first to ensure entry points are colored before their blocks are referenced

    if len(module_data['declarations']) > 0:

        for declaration in module_data['declarations']:

            # Generate NOMNOML for this declaration using the | separator in NOMNOML

            module_nomnoml = module_nomnoml + '|' + process_declaration(module_data['declarations'][declaration],
                                                                        declaration, entry_points,
                                                                        current_package, current_module, '')

        # Close our module declaration block

        module_nomnoml = module_nomnoml + ']\n'

        # Make our blocks a consistent size for visual clarity

        module_nomnoml = beautify_declaration_markup(module_nomnoml)

        # Use the --> NOMNOML dependency connector to show a dependency for the current module

        for dependency in module_data['dependencies']:

            module_nomnoml = module_nomnoml + '[' + current_module + ']-->[' + dependency + ']\n'


    # If we don't have any function or class declarations in this module
    else:

        # Process all of our dependencies using the --> separator

        module_nomnoml = module_nomnoml + ']\n'

        for index, dependency in enumerate(module_data['dependencies']):

            module_nomnoml = module_nomnoml + '[' + current_module + ']-->[' + dependency + ']\n'

    return module_nomnoml


def process_declaration(declaration_data: dict, declaration: str, entry_points: list, current_package: str,
                        # Test
                        current_module: str, declaration_nomnoml: str) -> str:
    """Generate NOMNOML for the current object's declaration
       Make a recursive call if we encounter a nested declaration inside of the original scope"""

    logging.getLogger('GUM Dispenser').debug('Processing declaration data: ' + str(declaration_data))

    # Read in the name of our scope and check if it is an entry point

    scope_name = declaration_data['current_scope_name']

    # Entry point checking for packaged code

    if current_package != '':

        if current_package + '.' + current_module + ':' + scope_name in entry_points:

            declaration_nomnoml = declaration_nomnoml + '[<entry>' + declaration + '|'

        else:

            declaration_nomnoml = declaration_nomnoml + '[' + declaration + '|'

    # Entry point checking for unpackaged code
    else:

        if current_module + ':' + scope_name in entry_points:

            declaration_nomnoml = declaration_nomnoml + '[<entry>' + declaration + '|'

        else:

            declaration_nomnoml = declaration_nomnoml + '[' + declaration + '|'

    # Search for and handle any nested declarations
    for key, value in declaration_data.items():

        if type(value) == dict:

            logging.getLogger('GUM Dispenser').debug('Found nested declaration: ' + key)

            declaration_nomnoml = declaration_nomnoml + '['

            declaration_nomnoml = declaration_nomnoml + process_declaration(value, key, entry_points,
                                                                            current_package, current_module, '') + '|'

    # Remove trailing separator characters
    if declaration_nomnoml[-1] == '|':

        declaration_nomnoml = declaration_nomnoml[:-1]

    # Close our declaration
    return declaration_nomnoml + ']'


def beautify_declaration_markup(markup : str) -> str:
    """Format our function and class declarations in NOMNOML to be a consistent size"""

    # We do not want to break before separators or before the end of a word
    # A 'word' in this case may include a trailing colon
    # Also catch function annotations with ->

    logging.getLogger('GUM Dispenser').debug('Beginning to beautify: ' + markup)

    pattern = re.compile(r"""(\|)|(\[[^\s|]+)|([\w:'",]+[\])]*\s*->)|([\w:'",]+[\])]*)""", re.MULTILINE)

    # Track how many characters we have read after last \n was inserted
    characters_read_in_current_line = 0

    # Track how many \n characters we have added
    new_lines_added = 0

    for match in re.finditer(pattern, markup):

        # Ignore empty string matches

        if match.group() != '':

            # Get how long the current match string is

            current_match_bounds = match.span()

            # Break if we have read 60 or more characters and we are not at a separator

            if characters_read_in_current_line > 59 and match.group() != '|':

                logging.getLogger('GUM Dispenser').debug('Inserting new line after ' + match.group())

                markup = markup[:current_match_bounds[1] + new_lines_added] + '\n' + \
                              markup[current_match_bounds[1] + new_lines_added:]

                # Reset our read characters

                characters_read_in_current_line = 0

                # Store that we have added a new line

                new_lines_added += 1


            else:

                # If we have finished a declaration and are more than two thirds of the way to 60 characters
                # Begin the next declaration on a new line

                if match.group() == '|' and characters_read_in_current_line > 39:

                    logging.getLogger('GUM Dispenser').debug('Inserting new line after ' + match.group())

                    markup = markup[:current_match_bounds[1] + new_lines_added] + '\n' + \
                             markup[current_match_bounds[1] + new_lines_added:]

                    # Reset our read characters

                    characters_read_in_current_line = 0

                    # Store that we have added a new line

                    new_lines_added += 1

                else:

                    # We have not reached 60 characters or 40 characters and the end of a declaration
                    # Track our progress in reading the string

                    characters_read_in_current_line += (current_match_bounds[1] - current_match_bounds[0])

    return markup
