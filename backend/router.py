"""
    discord-bot-2 backend

    Router receiver and sender threads

"""
import asyncio
import json
import logging
import secrets
from hashlib import md5
from typing import Tuple

import cachetools
import zmq
import zmq.asyncio
from redis import Redis, RedisError, ConnectionError

from .config import CONFIG
from .timing import Timer

logger = logging.getLogger("backend")


class Router:
    """
    Handle zmq interface
    """

    def __init__(self) -> None:
        self.__db = Redis(decode_responses=True)
        self.in_queue = "job_queue"
        self.out_queue = "response_queue"
        self.job_cache = cachetools.TTLCache(1000, 60)

        ctx = zmq.asyncio.Context()
        self.__sck = ctx.socket(zmq.ROUTER)
        address = CONFIG.get("startup", "zmq_address")
        self.__sck.bind(address)
        logger.info("Socket bound at %s", address)
        self.__sck.setsockopt(zmq.RCVTIMEO, 500)
        self.__sck.setsockopt(zmq.LINGER, 1000)

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
            finally:
                await asyncio.sleep(0.01)

    async def put_in_queue(self, msg: list, max_attempts: int = 5) -> None:
        """
        Puts a message in the input queue
        """
        for attempt in range(max_attempts):
            try:
                job_id = md5(secrets.token_bytes(8)).hexdigest()
                job = [job_id, *[x.hex() for x in msg]]
                self.__db.rpush(self.in_queue, json.dumps(job))
                self.__db.expire(self.in_queue, 60)
                self.job_cache[job_id] = None  # store ID as dict for faster lookup
                Timer.start(job_id)
                logger.info("[router] Queued job: %s", job_id)
                return
            except (RedisError, ConnectionError):
                logger.exception(
                    "An error occurred in Redis, retrying (attempt %s of %s)",
                    attempt + 1,
                    max_attempts,
                )
                await asyncio.sleep(0.2)

        raise Exception(f"Redis connection failure, retried {max_attempts} times")

    async def send(self) -> None:
        """
        Check for completed jobs and send until shutdown
        """
        while not self.is_shutting_down:
            try:
                job_id, msg = self.get_from_queue()
                if msg:
                    await self.__sck.send_multipart(msg)
                    logger.info("[router] Sent response, job took %sms", Timer.stop(job_id))
            except Exception as exc:
                logger.exception(exc)
                self.__sck.send_json({"code": 1})
            finally:
                await asyncio.sleep(0.01)

    def get_from_queue(self) -> Tuple[str, list]:
        """
        Get job ID and zmq message from Redis
        """
        msg = self.__db.lpop(self.out_queue)
        if msg:
            data = json.loads(msg)
            job_id = data[0]
            if job_id in self.job_cache:
                response = [bytes.fromhex(x) for x in data[1:]]
                del self.job_cache[job_id]
                return job_id, response
            logger.error("Job ID failed to validate. Fake job response?")
        return None, None
