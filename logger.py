"""Implemention of logger"""
import logging


def get_logger(name: str):
    """return logger"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s (%(name)s) %(levelname)s: %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
