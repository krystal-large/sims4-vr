import logging
from logging.handlers import RotatingFileHandler
import os
import sys
import traceback

def get_log_level(level_string):
    """
    Convert a string log level to a logging level constant.
    
    :param level_string: A string representing the log level (e.g., "DEBUG", "INFO")
    :return: The corresponding logging level constant
    """
    level_string = level_string.upper()
    logging_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    return logging_levels.get(level_string, logging.INFO)  # Default to INFO if not recognized

def setup_logger(log_dir, log_file, log_level_string):
    """
    Set up and return a logger with the specified configuration.
    
    :param log_dir: Directory where log files will be stored
    :param log_file: Name of the log file
    :param log_level_string: Logging level as a string (e.g., "DEBUG", "INFO")
    :return: Configured logger object
    """
    # Ensure the log directory exists
    os.makedirs(log_dir, exist_ok=True)
    
    # Create the full path for the log file
    log_path = os.path.join(log_dir, log_file)
    
    # Convert string log level to logging constant
    log_level = get_log_level(log_level_string)
    
    # Create a logger
    logger = logging.getLogger('sims4_vr_mod')
    logger.setLevel(log_level)
    
    # Create a rotating file handler
    file_handler = RotatingFileHandler(log_path, maxBytes=5*1024*1024, backupCount=5)
    file_handler.setLevel(log_level)
    
    # Create a formatter and add it to the handler
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Add the handler to the logger
    logger.addHandler(file_handler)
    
    return logger

def setup_exception_logging(logger):
    """
    Set up global exception handling to log unhandled exceptions.
    
    :param logger: The logger object to use for logging exceptions
    """
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # Call the default handler for KeyboardInterrupt
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Log the exception
        logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        
        # Optionally, you can also print the error to stderr
        print("An unhandled exception occurred:", file=sys.stderr)
        traceback.print_exception(exc_type, exc_value, exc_traceback)

    # Set the global exception handler
    sys.excepthook = handle_exception