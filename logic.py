import asyncio
import threading
import time
from typing import Callable
from pathlib import Path
from queue import Queue, PriorityQueue
import color_filter
from keyboard import add_hotkey
from asyncio import create_task, to_thread
from configobj import ConfigObj
from dataclasses import dataclass, field
from active_window_checker import WindowInfo
from inversion_rules import InversionRulesController
from realtime_data_sync import ConfigFileManager, RulesFileManager
import inject


class App:
    def __init__(self):
        from auto_update import AutoUpdater
        self.config_manager = ConfigFileManager("config")
        self.config = self.config_manager.config
        self.inversion_rules = InversionRulesController()
        self.inversion_rules_file_manager = RulesFileManager("inversion", self.inversion_rules)
        self.state_controller = FilterStateController()
        self.interaction_manager = InteractionManager()
        self.updater = AutoUpdater()
        inject.configure(self.configure)
        self.callbacks: PriorityQueue[App.Callback] = PriorityQueue()
        self.updater.on_update_applied = self.handle_update
        self.is_running = True
        self.window_switch_listener_thread = [None]

    async def run(self):
        from active_window_checker import listen_switch_events

        tasks = []
        tasks.append(create_task(to_thread(
            listen_switch_events,
            self.state_controller.on_active_window_switched,
            self.window_switch_listener_thread
        )))

        self.interaction_manager.setup()
        tasks.append(create_task(
            self.interaction_manager.run_tray()
        ))
        tasks.append(create_task(
            self.run_callbacks()
        ))
        self.updater.run_check_loop()
        print("I'm async")
        try:
            await asyncio.gather(*tasks)
        except asyncio.exceptions.CancelledError:
            pass
        print("Bye")

    async def run_callbacks(self):
        while self.is_running:
            callback = self.callbacks.get()
            callback.func()

    def close(self):
        import win32con
        import win32api
        if self.redirect_to_main_thread(self.close, priority=0):
            return
        self.is_running = False
        win32api.PostThreadMessage(
            self.window_switch_listener_thread[0],
            win32con.WM_QUIT, 0, 0
        )
        for task in asyncio.all_tasks():
            task.cancel()

    def handle_update(self,
                      new_path: Path,
                      current_path: Path,
                      backup_filename: str):
        try:
            from shutil import copyfile
            from os import path

            copy_list = [
                self.config.filename,
                self.inversion_rules_file_manager.filename
            ]

            for filename in copy_list:
                current_file_path = path.join(current_path, filename)
                new_file_path = path.join(new_path, filename)
                if path.exists(current_file_path):
                    if not path.exists(new_file_path):
                        copyfile(current_file_path, new_file_path)
                    else:
                        print(f"Skip {filename}: update contains same file")
                else:
                    print(f"Skip {filename}: no such file")

        except Exception as e:
            print("Failed to copy previous version data:", e)
            print("You may do this manually, from", backup_filename)
            print("Files to copy:", copy_list)

    def configure(self, binder: inject.Binder):
        components = (
            self.config,
            self.inversion_rules,
            self.inversion_rules_file_manager,
            self.state_controller,
            self.interaction_manager,
            self.updater,
            self,
        )
        for component in components:
            binder.bind(component.__class__, component)

    def redirect_to_main_thread(self, func, *args, priority=10, **kwargs):
        if threading.current_thread() != threading.main_thread():
            callback = App.Callback(priority,
                                    lambda: func(*args, **kwargs))
            self.callbacks.put_nowait(callback)
            return True
        return False

    @dataclass(order=True)
    class Callback:
        priority: int
        func: Callable = field(compare=False)


class FilterStateController:
    config = inject.attr(ConfigObj)
    rules = inject.attr(InversionRulesController)

    def __init__(self):
        from collections import deque
        self.last_active_windows = deque(maxlen=10)
        self.last_active_window = None

    def on_active_window_switched(self,
                                  hWinEventHook,
                                  event,
                                  hwnd,
                                  idObject,
                                  idChild,
                                  dwEventThread,
                                  dwmsEventTime):
        from active_window_checker import get_window_info, eventTypes

        if idObject != 0:
            return
        result = get_window_info(hwnd)
        if not result:
            return
        winfo = self.last_active_window = result
        self.last_active_windows.append(winfo)
        if self.config["display"]["show_events"]:
            print(winfo.path, eventTypes.get(event, hex(event)))
        color_filter.set_active(self.rules.is_inversion_required(winfo))


class InteractionManager:
    state_controller = inject.attr(FilterStateController)
    rules_controller = inject.attr(InversionRulesController)
    app = inject.attr(App)

    def __init__(self):
        from gui import Tray
        self.tray = Tray()

    def setup(self):
        from win32api import SetConsoleCtrlHandler
        SetConsoleCtrlHandler(self._process_exit_handler, True)
        initial_hotkey = 'ctrl+alt+'

        hotkeys = {
            'plus': self.append_current_app,
            'subtract': self.delete_current_app,
        }

        for k, v in hotkeys.items():
            add_hotkey(initial_hotkey + k, v)

    def close(self):
        self.app.close()

    def _process_exit_handler(self, signal):
        # Even if main thread busy, tray must be closed
        self.tray.close()
        self.close()
        time.sleep(1)  # Give time for tray to close
        return True  # Prevent next handler to run

    async def run_tray(self):
        try:
            await to_thread(self.tray.run)
        finally:
            self.tray.close()

    def append_current_app(self, winfo: WindowInfo = None):
        from gui import RuleCreationWindow

        if self.app.redirect_to_main_thread(
                self.append_current_app):
            return

        winfo = winfo or self.state_controller.last_active_window
        if not winfo:
            return
        rule, name = RuleCreationWindow(winfo).run()
        if name is not None and rule:
            self.rules_controller.add_rule(name, rule)

    def delete_current_app(self, winfo: WindowInfo = None):
        from gui import RuleRemovingWindow

        if self.app.redirect_to_main_thread(
                self.delete_current_app):
            return

        winfo = winfo or self.state_controller.last_active_window
        if not winfo:
            return
        if not self.rules_controller.is_inversion_required(winfo):
            return

        rules = RuleRemovingWindow(list(
            self.rules_controller.get_active_rules(winfo, self.rules_controller.rules)
        )).run()
        if rules:
            self.rules_controller.remove_rules(rules)

    def choose_window_to_remove_rules(self):
        from gui import ChooseRemoveCandidateWindow

        if self.app.redirect_to_main_thread(
                self.choose_window_to_remove_rules):
            return

        if not self.state_controller.last_active_window:
            return
        winfo = ChooseRemoveCandidateWindow(list(
            self.state_controller.last_active_windows
        )).run()
        if winfo:
            self.delete_current_app(winfo)

    def choose_window_to_make_rule(self):
        from gui import ChooseAppendCandidateWindow

        if self.app.redirect_to_main_thread(
                self.choose_window_to_make_rule):
            return

        if not self.state_controller.last_active_window:
            return
        winfo = ChooseAppendCandidateWindow(list(
            self.state_controller.last_active_windows
        )).run()
        if winfo:
            self.append_current_app(winfo)

    def request_update(self,
                       latest,
                       file_size,
                       developer_mode: bool,
                       response: Queue):
        from gui import UpdateRequestWindow

        if self.app.redirect_to_main_thread(
                self.request_update, latest,
                file_size, developer_mode, response):
            return

        response.put_nowait(UpdateRequestWindow(
            latest, file_size, developer_mode
        ).run())
