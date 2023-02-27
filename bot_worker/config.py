"""
    discord-bot-2 backend

   Global variables from config files

"""
import configparser
import logging
import os


def load_config() -> configparser.ConfigParser:
    filename = (
        "config/test_config.cfg" if os.environ.get("TESTING") else "/etc/bot-worker/config.cfg"
    )
    config = configparser.ConfigParser()
    config.read(filename)
    return config


CONFIG = load_config()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CONFIG.get("startup", "google_api_key")


def setup_logging() -> None:
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(CONFIG.get("startup", "log_file_dir"))
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("[%(asctime)s]-[%(funcName)s]-[%(levelname)s]: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
