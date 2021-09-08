"""
    discord-bot-2 backend
"""
import logging
import time
import traceback

import zmq

from backend.config import CONFIG
from backend.commands import handle_command

logger = logging.getLogger("backend")
NS_IN_MS = 1000000

class Router:
    """
    Handle zmq interface
    """
    def __init__(self):
        ctx = zmq.Context()
        self.sck = ctx.socket(zmq.REP)
        address = CONFIG.get("general", "zmq_address")
        self.sck.bind(address)
        logger.info("Socket bound at %s", address)
        self.sck.setsockopt(zmq.RCVTIMEO, 1000)

    def receive(self):
        """
        Receive, validate and handle message
        """
        try:
            msg = self.sck.recv_json()
            command, params = validate_msg(msg)
            logger.info("Received a command: %s", command)
        except zmq.Again:
            return
        except Exception as exc:
            logger.error(exc)
            logger.error(traceback.format_exc())
            self.sck.send_json({"code": 1})
            return

        start = time.time_ns()
        res = handle_command(command, params)
        logger.info("Time taken: %fms", (time.time_ns()-start)/NS_IN_MS)
        self.sck.send_json(res)

def validate_msg(msg):
    """
    Check required keys in message
    """
    params = msg.get("params")
    command = msg.get("command")
    if not command or not params:
        raise Exception("Message failed to validate")
    return command, params
