"""
    discord-bot-2 backend

    Worker thread

"""
import asyncio
import json
import logging

from redis import Redis, RedisError, ConnectionError

from .commands import API_COMMANDS, handle_command

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
        self.client_map = "client_map"
        self.is_shutting_down = False
        self.msg_len = 3

    @property
    def wid(self):
        return self.__wid

    async def run(self) -> None:
        """
        Try to process jobs from queue until shutdown
        """
        logger.info("%s started", self.wid)
        while not self.is_shutting_down:
            try:
                work = self.get_work()
                if work:
                    job_id, client, msg = work
                    validate_msg(msg)
                    response = await handle_command(*msg.values())
                    await self.put_response(job_id, client, response)
                    logger.info("[%s] Completed job: %s", self.__wid, job_id)
                await asyncio.sleep(0.01)
            except Exception as exc:
                logger.exception("[%s] An error occurred processing job: %s", self.__wid, exc)
                await asyncio.sleep(0.5)

    def get_work(self) -> tuple[str, bytes, dict] | None:
        """Grab work from redis queue"""
        msg = self.__db.lpop(self.in_queue)
        if msg:
            job = json.loads(msg)
            self.msg_len = len(job)
            if self.msg_len == 4:
                client, _, work = [bytes.fromhex(x) for x in job[1:]]
                return job[0], client, json.loads(work)
            if self.msg_len == 3:
                client, work = [bytes.fromhex(x) for x in job[1:]]
                return job[0], client, json.loads(work)
            else:
                raise Exception("Message malformed")
        return None

    async def put_response(
        self,
        job_id: str,
        client: bytes,
        response: dict,
        max_attempts=5,
    ) -> None:
        """Put response in redis queue"""
        for attempt in range(max_attempts):
            try:
                msg = None
                if self.msg_len == 4:
                    msg = [job_id, client.hex(), "", json.dumps(response).encode().hex()]
                if self.msg_len == 3:
                    msg = [job_id, client.hex(), json.dumps(response).encode().hex()]
                self.__db.rpush(self.out_queue, json.dumps(msg))
                self.__db.expire(self.out_queue, 60)
                return
            except (RedisError, ConnectionError):
                logger.exception(
                    "[%s] An error occurred in Redis, retrying (attempt %s of %s)",
                    self.__wid,
                    attempt + 1,
                    max_attempts,
                )
                await asyncio.sleep(0.2)

        raise Exception(f"Redis connection failure, retried {max_attempts} times")


def validate_msg(msg: dict) -> None:
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
