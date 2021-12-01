"""
    discord-bot-backend
"""
import logging


def setup_logger():
    logger = logging.getLogger("backend")
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("[%(asctime)s]-[%(funcName)s]-[%(levelname)s]: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
