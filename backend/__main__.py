"""
    discord-bot-2 backend

    Main entry point to run server

"""
import asyncio
from asyncio.windows_events import WindowsSelectorEventLoopPolicy

from .server import run_server

if __name__ == "__main__":
    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())  # windows specific thing
    asyncio.run(run_server())
