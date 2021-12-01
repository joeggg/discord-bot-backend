"""
    discord-bot-2 backend
"""

import asyncio

from asyncio.windows_events import WindowsProactorEventLoopPolicy

from backend.main import run_server

if __name__ == "__main__":
    asyncio.set_event_loop_policy(WindowsProactorEventLoopPolicy())
    asyncio.run(run_server())
