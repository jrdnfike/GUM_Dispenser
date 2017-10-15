
from GUM_Dispenser.GUM_Exceptions import ConfigurationNotFoundError, UserConfirmedInvalidSetup

import re

import os

import ast

from pathlib import Path

import logging

import token

from tokenize import tokenize
from io import BytesIO


def check_setup_size(setup_path : str) -> dict:
    """Ensure the size of our setup file is expected
    Avoid potential buffer overflows"""

    setup_specs = {}

    # Get file size

    setup_size = os.stat(setup_path + '/setup.py').st_size

    logging.getLogger('GUM Dispenser').info("Found setup.py with size " + str(setup_size) + " bytes")

    setup_specs['size'] = setup_size

    # setup.py should be a small file
    # Prompt to continue if > 2 KB
    if setup_size > 2000:

        setup_specs['valid_size'] = False

    else:

        setup_specs['valid_size'] = True

    return setup_specs


def handle_invalid_setup_size(setup_path : str) -> None:
    """Prompts user whether to continue if setup file
    is  unexpectedly large"""

    prompt_for_confirmation = input('Unexpectedly large setup file. Please check ' +
                                    'to ensure that\n' + str(Path(setup_path).joinpath('setup.py')) +
                                    ' is the correct file.\nIf this is correct, type Yes and hit enter.\n')

    if prompt_for_confirmation.lower() != 'yes':

        raise UserConfirmedInvalidSetup


def read_setup_contents(setup_path: str, setup_specs: dict) -> dict:
    """Read the setup file and remove extraneous whitespace from token list"""

    project_info = {}

    with open(setup_path + '/setup.py', 'r') as configFile:

        setup_contents = configFile.read(setup_specs['size'])

        logging.getLogger('GUM Dispenser').debug('Setup contents: \n' + str(setup_contents))

    # Tokenize is a generator, so we must iterate line by line over the text to get the tokenized version
    tokens = tokenize(BytesIO(setup_contents.encode('utf-8')).readline)

    current_assignment = ''

    for token_type, token_str, start, end, line_text in tokens:

        # Convert type from integer to string

        token_name = token.tok_name[token_type]

        logging.getLogger('GUM Dispenser').debug(str(start) + ',' + str(end) + ':\t' + token_name +
                                                 '\t' + line_text.strip())

        logging.getLogger('GUM Dispenser').debug('Current assignment: ' + current_assignment)

        # Process found entry points

        if current_assignment == 'entry_points':

            # We only care about assignment statements within the entry_points dictionary

            if token_name == 'STRING' and '=' in token_str:

                # Remove quote characters

                found_entry_point = ast.literal_eval(token_str)

                # The value of the assignment is the entry point

                found_entry_point = found_entry_point.split('=')[1].strip()

                logging.getLogger('GUM Dispenser').info('Found entry point ' + found_entry_point)

                project_info['entry_points'].append(found_entry_point)

            # Reset assignment if we come to the end of the entry points dictionary

            elif line_text.strip() == '}':

                current_assignment = ''


        # Catch if we are declaring packages, modules or entry_points
        elif token_name == 'NAME':

            # Make the appropriate key string
            # We append _names to avoid confusion in reading later processing code

            if token_str == 'packages' or token_str == 'modules' or token_str == 'entry_points':

                if token_str == 'packages' or token_str == 'modules':

                    current_assignment = token_str[:-1] + '_names'

                else:

                    current_assignment = token_str

                project_info[current_assignment] = []

        elif token_name == 'STRING':

            # Store packages or modules

            if current_assignment == 'package_names' or current_assignment == 'module_names':

                found_object_name = ast.literal_eval(token_str)

                logging.getLogger('GUM Dispenser').info('Adding ' + found_object_name + ' to ' + current_assignment)

                project_info[current_assignment].append(found_object_name)


        # Reset current assignment if we come to the end of a list of packages or modules

        elif (current_assignment == 'package_names' or current_assignment == 'module_names') and token_str == ']':

            logging.getLogger('GUM Dispenser').debug('Resetting current assignment from ' + current_assignment)

            current_assignment = ''



    return project_info


def parse_setup(setup_path: str) -> dict:
    """Parses the given setup.py file"""

    # Validate setup.py size

    setup_specs = check_setup_size(setup_path)

    if not setup_specs['valid_size']:

        handle_invalid_setup_size(setup_path)



    logging.getLogger('GUM Dispenser').info("Reading " + str(setup_specs['size'])
                                            + " bytes from setup.py...")

    # Get token contents of setup.py

    setup_condensed = read_setup_contents(setup_path, setup_specs)


    # User must define which files will be read

    if 'package_names' not in setup_condensed and 'module_names' not in setup_condensed:

        raise ConfigurationNotFoundError

    # Warn no entry points are found

    if 'entry_points' not in setup_condensed:

        logging.getLogger('GUM Dispenser').warning('You do not have an entry point set for your package in setup.py.\n')

        setup_condensed['entry_points'] = []

    return setup_condensed
