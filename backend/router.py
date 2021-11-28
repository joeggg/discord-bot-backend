"""
    discord-bot-2 backend
"""

import asyncio
import logging
import secrets

import cachetools
from google.api_core.gapic_v1 import client_info
import zmq
import zmq.asyncio

from redis import Redis, RedisError

from backend.config import CONFIG

logger = logging.getLogger("backend")


class Router:
    """
    Handle zmq interface
    """

    def __init__(self) -> None:
        self.__db = Redis(decode_responses=True)
        self.in_queue = "job_queue"
        self.out_queue = "response_queue"
        self.job_map = "job_map"
        self.resp_map = "response_map"
        self.client_map = cachetools.TTLCache(1000, 60)

        ctx = zmq.asyncio.Context()
        self.__sck = ctx.socket(zmq.ROUTER)
        address = CONFIG.get("general", "zmq_address")
        self.__sck.bind(address)
        logger.info("Socket bound at %s", address)
        self.__sck.setsockopt(zmq.RCVTIMEO, 100)
        self.__sck.setsockopt(zmq.LINGER, 100)

        self.is_shutting_down = False
        self.client = None

    async def recv(self) -> None:
        """
        Poll for received commands until shutdown
        """
        while not self.is_shutting_down:
            try:
                msg = await self.__sck.recv_multipart()
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
                job_id = secrets.token_hex(8)
                with self.__db.pipeline() as pipe:
                    pipe.rpush(self.in_queue, job_id)
                    pipe.expire(self.in_queue, 60)
                    pipe.hset(self.job_map, job_id, msg[2])
                    pipe.expire(self.job_map, 60)
                    pipe.execute()

                self.client_map[job_id] = msg[0]
                logger.info("[router] Queued job: %s", job_id)
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
                client, response = self.get_from_queue()
                if client:
                    await self.__sck.send_multipart(
                        [client, b"", bytes(response, encoding="utf8")],
                    )
                    logger.info("[router] Sent response")
                    continue
                await asyncio.sleep(0.01)
            except Exception as exc:
                logger.exception(exc)
                self.__sck.send_json({"code": 1})

    def get_from_queue(self) -> str:
        job_id = self.__db.lpop(self.out_queue)
        if job_id:
            response = self.__db.hget(self.resp_map, job_id)
            self.__db.hdel(self.resp_map, job_id)
            return self.client_map.get(job_id), response
        return None, None
