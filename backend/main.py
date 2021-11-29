"""
    discord-bot-2 backend
"""

import asyncio
import logging

from backend.config import CONFIG
from backend.google_handler import GoogleHandler
from backend.logger import setup_logger
from backend.router import Router
from backend.worker import Worker

logger = logging.getLogger("backend")


async def run_server():
    """
    Main running loop
    """
    setup_logger()
    num_workers = CONFIG.getint("general", "num_workers")
    GoogleHandler.initialise()
    router = Router()

    futures = [
        *[Worker(i).run() for i in range(num_workers)],
        router.recv(),
        router.send(),
    ]

    await asyncio.gather(*futures)
