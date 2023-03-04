"""
    discord-bot-2 backend

   Global variables from config files

"""
import configparser
from dataclasses import dataclass
import json
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


@dataclass
class RedditConfig:
    subreddits: list[str]
    creds: dict[str, str]
    auth_headers: dict[str, str]
    auth_time: float


def load_reddit_config() -> RedditConfig:
    with open(f'{CONFIG.get("startup", "data_path")}/subreddits.txt', "r") as fp:
        subreddits = [line.strip() for line in fp if line]

    with open(CONFIG.get("startup", "reddit_creds"), "r") as fp:
        creds = json.load(fp)

    return RedditConfig(subreddits, creds, {}, 0.0)


REDDIT_CONF = load_reddit_config()


def setup_logging() -> None:
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(CONFIG.get("startup", "log_file_dir"))
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("[%(asctime)s]-[%(funcName)s]-[%(levelname)s]: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
