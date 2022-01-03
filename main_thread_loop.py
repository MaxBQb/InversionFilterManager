import threading
from dataclasses import dataclass, field
from queue import PriorityQueue
from typing import Callable

import inject

from utils import show_exceptions


@dataclass(order=True)
class Callback:
    func: Callable = field(compare=False)
    priority: int = 10


def is_main_thread():
    return threading.current_thread() == threading.main_thread()


class MainExecutor:
    def __init__(self):
        self.callbacks: PriorityQueue[Callback] = PriorityQueue()
        self._alive = True

    async def run_loop(self):
        if not is_main_thread():
            raise RuntimeError()

        while self._alive:
            with show_exceptions():
                callback = self.callbacks.get()
                callback.func()

    def send_callback(self, callback: Callback):
        self.callbacks.put_nowait(callback)

    def close(self):
        self._alive = False


def execute_in_main_thread(priority: int = 10):
    def _decorator(func):
        def _wrapper(*args, **kwargs):
            if is_main_thread():
                # Note that if thread is not main
                # Then return value is None
                return func(*args, **kwargs)

            inject.instance(MainExecutor).send_callback(Callback(
                (lambda: func(*args, **kwargs))
                if args or kwargs else func,
                priority
            ))
        return _wrapper
    return _decorator
