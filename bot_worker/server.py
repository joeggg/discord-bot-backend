"""
    discord-bot-2 backend

    Top-level server functions    

"""
import asyncio
import logging
import time

from .config import CONFIG, setup_logging
from .google_handler import GoogleHandler
from .router import Router
from .worker import Worker


async def heartbeat():
    heartbeat_interval = CONFIG.getint("startup", "heartbeat_interval_s")
    start = time.time()
    while True:
        if time.time() - start > heartbeat_interval:
            start = time.time()
            logging.info("[main] HEARTBEAT")
        await asyncio.sleep(5)


async def run_server():
    """
    Main running loop
    """
    setup_logging()
    num_workers = CONFIG.getint("startup", "num_workers")
    GoogleHandler.initialise()
    router = Router()
    logging.info("Starting server")

    futures = [
        *[Worker(i).run() for i in range(num_workers)],
        router.recv(),
        router.send(),
        heartbeat(),
    ]

    await asyncio.gather(*futures)
