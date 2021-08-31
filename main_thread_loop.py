import threading
from dataclasses import dataclass, field
from queue import PriorityQueue
from typing import Callable
import inject


@dataclass(order=True)
class Callback:
    func: Callable = field(compare=False)
    priority: int
    last: bool = field(compare=False)


def is_main_thread():
    return threading.current_thread() == threading.main_thread()


class MainExecutor:
    def __init__(self):
        self.callbacks: PriorityQueue[Callback] = PriorityQueue()

    async def run_loop(self):
        if not is_main_thread():
            raise RuntimeError()

        while True:
            callback = self.callbacks.get()
            callback.func()
            if callback.last:
                break

    def send_callback(self, callback: Callback):
        self.callbacks.put_nowait(callback)


def execute_in_main_thread(priority: int = 10,
                           last: bool = False):
    def _decorator(func):
        def _wrapper(*args, **kwargs):
            if is_main_thread():
                # Note that if thread is not main
                # Then return value is None
                return func(*args, **kwargs)

            inject.instance(MainExecutor).send_callback(Callback(
                lambda: func(*args, **kwargs),
                priority, last
            ))
        return _wrapper
    return _decorator
