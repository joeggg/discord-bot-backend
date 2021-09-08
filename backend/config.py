"""
    discord-bot-2 backend
"""
import configparser
import json

def load_config():
    config = configparser.ConfigParser()
    config.read("config/config.cfg")
    return config

def load_voice_presets():
    with open("data/voice_presets.json", "r") as file:
        preset_data = json.load(file)
        return preset_data

CONFIG = load_config()
VOICE_PRESETS = load_voice_presets()
