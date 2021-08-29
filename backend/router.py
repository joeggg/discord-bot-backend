"""
    discord-bot-2 backend
"""
import time
import traceback

import zmq

from backend.config import CONFIG
from backend.commands import handle_command

class Router:
    """
    Handle zmq interface
    """
    def __init__(self):
        ctx = zmq.Context()
        self.sck = ctx.socket(zmq.REP)
        self.sck.bind(CONFIG.get("general", "zmq_address"))
        print(f"Socket bound")
        self.sck.setsockopt(zmq.RCVTIMEO, 1000)

    def receive(self):
        try:
            msg = self.sck.recv_json()
            command, params = validate_msg(msg)
            print(f"Received a command: {command}")
        except zmq.Again:
            return
        except Exception as exc:
            print(exc)
            traceback.print_exc()
            self.sck.send_json({"status": "failure"})
            return

        start = time.time()
        res = handle_command(command, params)
        print(f"Time taken: {1000*(time.time()-start)}ms")
        self.sck.send_json({"status": res})

def validate_msg(msg):
    """
    Check required keys in message
    """
    params = msg.get("params")
    command = msg.get("command")
    if not command or not params:
        raise Exception("Message failed to validate")
    return command, params
