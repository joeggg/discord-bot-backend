"""
    discord-bot-2 backend

   Global variables from config files

"""
import configparser
import json
import os


def load_config():
    filename = (
        "config/test_config.cfg" if os.environ.get("TESTING") else "/etc/bot-worker/config.cfg"
    )
    config = configparser.ConfigParser()
    config.read(filename)
    return config


CONFIG = load_config()


def load_voice_presets():
    with open(f'{CONFIG.get("startup", "data_path")}/voice_presets.json', "r") as file:
        preset_data = json.load(file)
        return preset_data


VOICE_PRESETS = load_voice_presets()
