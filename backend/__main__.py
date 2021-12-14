"""
    discord-bot-2 backend

    Main entry point to run server

"""
import asyncio

from .server import run_server

if __name__ == "__main__":
    # from asyncio.windows_events import WindowsSelectorEventLoopPolicy
    # asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())  # uncomment for windows
    asyncio.run(run_server())
