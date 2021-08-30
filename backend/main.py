"""
    discord-bot-2 backend
"""
import logging
import time

from backend.config import CONFIG
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
    router = Router()
    
    while 1:
        router.receive()
        if (time.time() - start) > heartbeat_interval:
            logger.debug("HEARTBEAT")
            start = time.time()
