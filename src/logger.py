import logging
from rich.logging import RichHandler


def get_logger(name: str = None):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = RichHandler()
    logger.addHandler(handler)
    return logger