"""
    discord-bot-backend

    Logger setup

"""
import logging

from .config import CONFIG


def setup_logger():
    logger = logging.getLogger("backend")
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(CONFIG.get("startup", "log_file_dir"))
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("[%(asctime)s]-[%(funcName)s]-[%(levelname)s]: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
