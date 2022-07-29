import asyncio
import time
from typing import Callable

import inject
import win32api
from win32con import WM_QUIT

from main_thread_loop import execute_in_main_thread, MainExecutor


class AppCloseManager:
    def __init__(self):
        self._blocked_threads: list[int] = []
        self._on_exit_routines: list[Callable] = []

    def append_blocked_thread(self):
        self._blocked_threads.append(win32api.GetCurrentThreadId())

    def add_exit_handler(self, handler: Callable):
        self._on_exit_routines.append(handler)

    def _run_exit_handlers(self):
        for handler in self._on_exit_routines:
            try:
                handler()
            except:
                pass

    def setup(self):
        win32api.SetConsoleCtrlHandler(self._process_exit_handler, True)

    def _process_exit_handler(self, signal):
        self.close()
        time.sleep(1)  # Give time for tray to close
        return True  # Prevent next handler to run

    def close(self):
        # Runs all exit handlers in current thread
        # Then stop app from main thread
        self._run_exit_handlers()
        self._close()

    @execute_in_main_thread(0)
    def _close(self):
        for thread_id in self._blocked_threads:
            win32api.PostThreadMessage(
                thread_id, WM_QUIT, 0, 0
            )

        for task in asyncio.all_tasks():
            task.cancel()

        inject.instance(MainExecutor).close()
