
import argparse

import os

from pathlib import Path

from GUM_Dispenser.GUM_Exceptions import InvalidSourcePathError, ConfigurationNotFoundError, PackageNotFoundError

from GUM_Dispenser.GUM_Exceptions import SourceModuleNotFoundError, UserConfirmedInvalidSetup

from GUM_Dispenser.GUM_setup_parser import parse_setup

from GUM_Dispenser.GUM_Describe_Source import describe_project

from GUM_Dispenser.GUM_Generate_NOMNOML import generate_project_nomnoml

import logging


def define_arguments() -> 'ArgumentParser':
    """Define command line arguments for GUM Dispenser"""

    arg_parser = argparse.ArgumentParser(description="Generates nomnoml from a source package")

    arg_parser.add_argument('--path', '-p', help='The path to the base development directory' 
                            + ' of or a package folder in your source code. Default is current working directory',
                            default=os.getcwd())

    arg_parser.add_argument('--setup_file', '-s', help='The path to the setup.py file. ' 
                             + 'If given, ignore any setup.py file found at --path and its parent for this file.'
                             + 'If not given, checks the value of --path and its immediate parent for setup.py',
                            default=None)

    arg_parser.add_argument('--debug', help='Flag to display debug level messages during execution',
                            action='store_true')

    return arg_parser


def initialize_log(arguments_received : dict) -> None:
    """Set up logging components and bind them together"""

    # Use our custom formatter
    main_formatter = logging.Formatter(fmt='%(asctime)s %(module)s.py: %(levelname)s - %(message)s')

    # Set up our handler
    main_handler = logging.StreamHandler()

    level_string = ''

    if arguments_received['debug']:
        level_string = 'DEBUG'
        main_handler.setLevel(level_string)
    else:
        level_string = 'INFO'
        main_handler.setLevel(level_string)

    main_handler.setFormatter(main_formatter)

    # Set up our logger
    main_logger = logging.getLogger('GUM Dispenser')

    if arguments_received['debug']:
        main_logger.setLevel(level_string)
    else:
        main_logger.setLevel(level_string)
    main_logger.addHandler(main_handler)

    logging.getLogger('GUM Dispenser').info('Welcome to GUM Dispenser!')
    logging.getLogger('GUM Dispenser').info('Logging level: ' + level_string)


def check_for_setup(arguments_received: dict) -> str:
    """Get the path to a nearby or specified setup.py file as a string"""

    setup_path_str = None

    # Check user supplied setup path if it is present

    if arguments_received['setup_file'] is not None and arguments_received['setup_file'] != '':

        setup_path_str = arguments_received['setup_file']

        setup_path = Path(setup_path_str)

        if setup_path.exists():

            # Find a setup.py file at or near the given path

            if setup_path.name == 'setup.py':

                logging.getLogger('GUM Dispenser').info('Setup found in given directory: ' + str(setup_path.parent))

                setup_path_str = str(setup_path.parent)

            elif setup_path.is_dir():

                if Path(setup_path).joinpath('setup.py').exists():

                    logging.getLogger('GUM Dispenser').info("Setup found in given directory: " + str(setup_path))

        else:

            logging.getLogger('GUM Dispenser').error('Given explicit setup.py path ' + str(setup_path) +
                                                     ' does not exist. Checking near development directory instead...')

            setup_path_str = None


    # User did not specify setup.py location or no file found near given path

    if setup_path_str is None:

        logging.getLogger('GUM Dispenser').info('No explicit input directory for setup.py. ' +
                                                'Checking near development directory...')


        # Check given directory and one level up for the setup file

        if Path(arguments_received['path']).joinpath('setup.py').exists():

            logging.getLogger('GUM Dispenser').info("Setup found in base development directory: " +
                                                    arguments_received['path'])

            setup_path_str = arguments_received['path']

        elif Path(arguments_received['path']).parent.joinpath('setup.py').exists():

            logging.getLogger('GUM Dispenser').info("Setup found in base development directory: " +
                                                    str(Path(arguments_received['path']).parent))

            setup_path_str = str(Path(arguments_received['path']).parent)


    # Require presence of a setup.py file
    if setup_path_str is None:

        raise ConfigurationNotFoundError


    return setup_path_str


def dispense_gum(arguments_received: dict) -> None:

    try:

        development_directory = Path(arguments_received['path']).resolve()  # Expand symbolic links

        # Input should be a directory

        if not development_directory.exists() or not development_directory.is_dir():

            raise InvalidSourcePathError

        setup_path = check_for_setup(arguments_received)


        # Read list of attributes and values used in setup.py, ignoring comments

        setup_distro_defs = parse_setup(setup_path)

        logging.getLogger('GUM Dispenser').debug(setup_distro_defs)


        # Get a dictionary full of relevant data for UML text generation

        uml_data = describe_project(setup_distro_defs, development_directory)

        logging.getLogger('GUM Dispenser').debug(uml_data)

        print(generate_project_nomnoml(uml_data, setup_distro_defs['entry_points']))



    except InvalidSourcePathError as err:
        logging.getLogger('GUM Dispenser').exception("The given source path was not found on your system.\n" +
                                                     "Choose a valid path or change " +
                                                     "your current directory to your local source package.")

    except ConfigurationNotFoundError as err:
        logging.getLogger('GUM Dispenser').exception("We couldn't find a complete project definition" +
                                                     " in your specified setup.py file.\n" +
                                                     "Specify either packages or modules in a setup.py file " +
                                                     "near your given source code path.")

    except PackageNotFoundError as err:

        logging.getLogger('GUM Dispenser').exception("The package " + str(err) +
                                                     " specified in your setup.py doesn't exist or is not a directory.")

    except SourceModuleNotFoundError as err:

        logging.getLogger('GUM Dispenser').exception('Missing or bad path for .py source file\n')


    except UserConfirmedInvalidSetup as err:

        logging.getLogger('GUM Dispenser').exception('User requested program termination. Goodbye')


    except Exception as err:

        logging.getLogger('GUM Dispenser').exception('Error: ' + str(err))




def main():

    input_parser = define_arguments()

    arguments_received = input_parser.parse_args()

    initialize_log(vars(arguments_received))

    dispense_gum(vars(arguments_received))
