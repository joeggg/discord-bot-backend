"""
    discord-bot-2 backend
"""
import logging
import time

from backend.config import CONFIG
from backend.google_handler import GoogleHandler
from backend.logging import setup_logger
from backend.router import Router

logger = logging.getLogger("backend")


def run_server():
    """
    Main running loop
    """
    start = time.time()
    setup_logger()
    heartbeat_interval = CONFIG.getint("general", "heartbeat_interval_s")
    GoogleHandler.initialise()
    router = Router()

    while 1:
        router.receive()
        if (time.time() - start) > heartbeat_interval:
            logger.debug("HEARTBEAT")
            start = time.time()
