"""
    discord-bot-2 backend
"""
import configparser

def load_config():
    config = configparser.ConfigParser()
    config.read("config/config.cfg")
    return config

CONFIG = load_config()
