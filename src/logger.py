# -*- coding: utf-8 -*-
import logging

from rich.logging import RichHandler


def get_logger(name: str = None, level: str = "INFO"):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = RichHandler()
    logger.addHandler(handler)
    return logger
