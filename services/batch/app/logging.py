import logging
import sys

def configure_logging(level: str = "INFO"):
    """
    Configure logging for the application.
    :param level: Logging level, default is 'INFO'.
    """
    level_obj = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        stream=sys.stdout,
        level=level_obj,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

def get_logger(name: str):
    """
    Helper to get a logger for a module.
    """
    return logging.getLogger(name)
