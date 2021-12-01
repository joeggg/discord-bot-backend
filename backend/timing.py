"""
    discord-bot-2 backend
 
    Timing utilities

"""
import functools
import logging
import time
from inspect import iscoroutinefunction
from typing import Optional

import cachetools


NS_IN_MS = 1000000

logger = logging.getLogger("backend")


class Timer:
    timers = cachetools.TTLCache(1000, 60)

    @classmethod
    def start(cls, key: str) -> None:
        cls.timers[key] = time.time_ns()

    @classmethod
    def stop(cls, key: str) -> Optional[float]:
        if key in cls.timers:
            elapsed_ns = time.time_ns() - cls.timers[key]
            del cls.timers[key]
            return elapsed_ns / NS_IN_MS
        return None


def timeit(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time_ns()
        func(*args, **kwargs)
        elapsed_ns = time.time_ns() - start
        logger.info("%s took %fms", func.__name__, elapsed_ns / NS_IN_MS)

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.time_ns()
        await func(*args, **kwargs)
        elapsed_ns = time.time_ns() - start
        logger.info("%s took %fms", func.__name__, elapsed_ns / NS_IN_MS)

    if iscoroutinefunction(func):
        return async_wrapper

    return wrapper
