"""
    Worker
"""

import asyncio
import json
import logging
import time
from typing import Tuple

from redis import Redis, RedisError

from backend.commands import API_COMMANDS, handle_command
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
        self.in_queue = "job_queue"
        self.out_queue = "response_queue"
        self.job_map = "job_map"
        self.resp_map = "response_map"
        self.client_map = "client_map"
        self.is_shutting_down = False
        self.heartbeat_interval = CONFIG.getint("general", "heartbeat_interval_s")
        self.current_client = ""

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
                job_id, work = self.get_work()
                if work:
                    validate_msg(work)
                    response = await handle_command(*work.values())
                    await self.put_response(job_id, response)
                    logger.info("[%s] Completed job: %s", self.__wid, job_id)
                    continue
                await asyncio.sleep(0.01)
            except Exception as exc:
                logger.exception("[%s] An error occurred processing job: %s", self.__wid, exc)
                await asyncio.sleep(0.5)

            if time.time() - start > self.heartbeat_interval:
                start = time.time()
                logger.info("[%s] HEARTBEAT", self.__wid)

    def get_work(self) -> Tuple[str, dict]:
        """Grab work from redis queue"""
        job_id = self.__db.lpop(self.in_queue)
        if job_id:
            data = self.__db.hget(self.job_map, job_id)
            self.__db.hdel(self.job_map, job_id)
            return job_id, json.loads(data)
        return None, None

    async def put_response(self, job_id: str, response: dict, max_attempts=5) -> None:
        """Put response in redis queue"""
        for attempt in range(max_attempts):
            try:
                with self.__db.pipeline() as pipe:
                    pipe.rpush(self.out_queue, job_id)
                    pipe.expire(self.out_queue, 60)
                    pipe.hset(self.resp_map, job_id, json.dumps(response))
                    pipe.expire(self.resp_map, 60)
                    pipe.execute()
                return
            except RedisError:
                logger.exception(
                    "[%s] An error occurred in Redis, retrying (attempt %s of %s)",
                    self.__wid,
                    attempt + 1,
                    max_attempts,
                )
                await asyncio.sleep(0.2)

        raise Exception(f"Redis connection failure, retried {max_attempts} times")


def validate_msg(msg: dict):
    """
    Check required keys in message
    """
    params = msg.get("params")
    command = msg.get("command")
    if command is None or params is None:
        raise Exception("Message failed to validate")

    if command not in API_COMMANDS:
        raise Exception("Command not in API commands")

    for param in API_COMMANDS[command]["params"]:
        if param not in params:
            err_msg = f"Missing param: {param}"
            logger.error(err_msg)
            raise Exception(err_msg)
