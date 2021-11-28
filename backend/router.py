"""
    discord-bot-2 backend
"""

import asyncio
import json
import logging

import zmq
import zmq.asyncio

from redis import Redis, RedisError

from backend.config import CONFIG
from backend.commands import API_COMMANDS

logger = logging.getLogger("backend")


class Router:
    """
    Handle zmq interface
    """

    def __init__(self) -> None:
        self.__db = Redis(decode_responses=True)
        self.in_key = "work_queue"
        self.out_key = "response_queue"
        ctx = zmq.asyncio.Context()
        self.__sck = ctx.socket(zmq.ROUTER)
        address = CONFIG.get("general", "zmq_address")
        self.__sck.bind(address)
        logger.info("Socket bound at %s", address)
        self.__sck.setsockopt(zmq.RCVTIMEO, 100)
        self.__sck.setsockopt(zmq.LINGER, 100)

        self.is_shutting_down = False

    async def recv(self) -> None:
        """
        Poll for received commands until shutdown
        """
        while not self.is_shutting_down:
            try:
                msg = await self.__sck.recv_json()
                validate_msg(msg)
                await self.put_in_queue(msg)
            except zmq.Again:
                pass
            except Exception as exc:
                logger.exception(exc)
                self.__sck.send_json({"code": 1})

    async def put_in_queue(self, msg: dict, max_attempts=5) -> None:
        """
        Puts a message in the input queue
        """
        for attempt in range(max_attempts):
            try:
                self.__db.rpush(self.in_key, json.dumps(msg))
                logger.info("Queued command: %s", msg)
                return
            except RedisError:
                logger.exception(
                    "An error occurred in Redis, retrying (attempt %s of %s)",
                    attempt + 1,
                    max_attempts,
                )
                await asyncio.sleep(0.2)

        raise Exception(f"Redis connection failure, retried {max_attempts} times")

    async def send(self):
        """
        Check for completed jobs and send until shutdown
        """
        while not self.is_shutting_down:
            try:
                msg = self.get_from_queue()
                if msg:
                    await self.__sck.send_json(msg)
                    logger.info("sent response")
                    continue
                await asyncio.sleep(0.1)
            except Exception as exc:
                logger.exception(exc)
                self.__sck.send_json({"code": 1})

    def get_from_queue(self) -> str:
        msg = self.__db.lpop(self.out_key)
        return msg


def validate_msg(msg: dict):
    """
    Check required keys in message
    """
    params = msg.get("params")
    command = msg.get("command")
    if not command or not params:
        raise Exception("Message failed to validate")

    for param in API_COMMANDS[command]["params"]:
        if param not in params:
            err_msg = f"Missing param: {param}"
            logger.error(err_msg)
            raise Exception(err_msg)
