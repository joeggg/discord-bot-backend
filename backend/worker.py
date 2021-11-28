"""
    Worker
"""

import asyncio
import json
import logging
import time

from typing import Tuple

from redis import Redis, RedisError

from backend.commands import handle_command
from backend.config import CONFIG

logger = logging.getLogger("backend")


class Worker:
    """
    Gets jobs from work queue and processes the request
    Puts results into response queue
    """

    def __init__(self, worker_id: int) -> None:
        self.__wid = f"worker:{worker_id}"
        self.__db = Redis(decode_responses=True)
        self.in_key = "work_queue"
        self.out_key = "response_queue"
        self.is_shutting_down = False
        self.heartbeat_interval = CONFIG.getint("general", "heartbeat_interval_s")

    @property
    def wid(self):
        return self.__wid

    async def run(self) -> None:
        """
        Try to process jobs from queue until shutdown
        """
        start = time.time()
        while not self.is_shutting_down:
            try:
                work = self.get_work()
                if work:
                    response = handle_command(*work.values())
                    await self.put_response(response)
                    logger.info("[%s] Completed job", self.__wid)
                    continue
                await asyncio.sleep(0.1)
            except Exception as exc:
                logger.exception("[%s] An error occurred processing work: %s", self.__wid, exc)
                await asyncio.sleep(0.5)

            if time.time() - start > self.heartbeat_interval:
                start = time.time()
                logger.info("[%s] HEARTBEAT", self.__wid)

    def get_work(self) -> dict:
        """Grab work from redis queue"""
        msg = self.__db.lpop(self.in_key)
        if msg:
            return json.loads(msg)

    async def put_response(self, response: dict, max_attempts=5) -> None:
        """Put response in redis queue"""
        for attempt in range(max_attempts):
            try:
                self.__db.rpush(self.out_key, json.dumps(response))
                return
            except RedisError:
                logger.exception(
                    "[%s] An error occurred in Redis, retrying (attempt %s of %s)",
                    self.__wid,
                    attempt + 1,
                    max_attempts,
                )
                await asyncio.sleep(1)

        raise Exception(f"Redis connection failure, retried {max_attempts} times")
