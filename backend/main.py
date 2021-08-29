"""
    discord-bot-2 backend
"""
import os
import time

from backend.config import CONFIG
from backend.router import Router

def run_server():
    """
    Main running loop
    """
    start = time.time()
    heartbeat_interval = CONFIG.getint("general", "heartbeat_interval_s")
    router = Router()
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f'{os.getcwd()}/{CONFIG.get("general", "google_api_key")}'
    print(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
    
    while 1:
        router.receive()
        if (time.time() - start) > heartbeat_interval:
            print(f"HEARTBEAT")
            start = time.time()

run_server()
