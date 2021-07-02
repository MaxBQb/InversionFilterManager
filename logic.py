import time
import pyautogui as gui
from watchdog.observers.api import DEFAULT_OBSERVER_TIMEOUT
from winregal import RegKey
from configobj import ConfigObj
from asyncio import create_task
from watchdog.observers import Observer


class App:
    def __init__(self):
        gui.FAILSAFE = False
        self.state_controller = FilterStateController(self)
        self.interaction_manager = InteractionManager(self)
        self.config = ConfigManager("config").get_config()
        self.rules = ConfigManager("rules").get_config(False)

    def run(self):
        from active_window_checker import listen_switch_events
        create_task(listen_switch_events(
            self.state_controller.on_active_window_switched
        ))
        self.interaction_manager.setup()


class AppElement:
    def __init__(self, app: App):
        self.app = app


class InversionFilterController:
    @staticmethod
    def is_active():
        with RegKey(r"HKEY_CURRENT_USER\Software\Microsoft\ColorFiltering") as key:
            return bool(key.get_value("Active").data)

    @staticmethod
    def set(value):
        if value != InversionFilterController.is_active():
            InversionFilterController.toggle()

    @staticmethod
    def toggle():
        gui.hotkey("ctrl", "win", "c")


class FilterStateController(AppElement):
    def on_active_window_switched(self,
                                  hWinEventHook,
                                  event,
                                  hwnd,
                                  idObject,
                                  idChild,
                                  dwEventThread,
                                  dwmsEventTime):
        from active_window_checker import get_window_info, eventTypes, getActiveWindow
        hwnd = getActiveWindow()
        self.last_active_window = get_window_info(hwnd, idObject, dwEventThread)
        title, processID, shortName, alt_hwnd = self.last_active_window
        if self.app.config["display"]["show_events"]:
            print(shortName, eventTypes.get(event, hex(event)))
        InversionFilterController.set(shortName == "System32\mspaint.exe")


class ConfigManager:
    def __init__(self, name: str):
        self.name = name
        self.observer = ConfigManager.LazyObserver()

    def get_config(self, write_defaults=True) -> ConfigObj:
        config = ConfigObj(infile=self.name + ".ini",
                           configspec=self.name + "_description.ini",
                           create_empty=True,
                           write_empty_values=True)
        self.invalidate_config(config, write_defaults)
        self.watch_config(config, write_defaults)
        return config

    def watch_config(self, config, write_defaults=True):
        from watchdog.events import PatternMatchingEventHandler
        handler = PatternMatchingEventHandler(patterns=[".\\" + config.filename],
                                              case_sensitive=True)

        def on_modified(event):
            config.reload()
            self.observer.sleep()
            if self.invalidate_config(config, write_defaults):
                print(f"Changes for '{config.filename}' applied")
            else:
                print(f"Changes for '{config.filename}' fixed & applied")
            self.observer.wakeup()

        handler.on_modified = on_modified
        self.observer.schedule(handler, ".", recursive=True)
        self.observer.start()

    @staticmethod
    def invalidate_config(config: ConfigObj, write_defaults=True):
        from validate import Validator
        test = config.validate(Validator(), copy=write_defaults, preserve_errors=True)
        check_failed = test is not True
        if test is False:
            config.restore_defaults()
            config.validate(Validator(), copy=write_defaults)
            print("Invalid configuration found.")
            print(f"Restore defaults for '{config.filename}'")
        elif check_failed:
            ConfigManager.invalidate_parts(config, test, write_defaults)
        config.initial_comment = ["Feel free to edit this config file"]
        config.write()
        return check_failed

    @staticmethod
    def invalidate_parts(config: ConfigObj, test: dict, write_defaults=True):
        from configobj import flatten_errors
        print("Invalid configuration parts found.")
        for sections, key, error in flatten_errors(config, test):
            if not error:
                error = "missing"
            pointer = config
            for section in sections:
                pointer = pointer[section]
            print('.'.join(sections + [key]) + ":", error)
            pointer.restore_default(key)
            if write_defaults:
                pointer[key] = pointer[key]  # current = default
        print(f"Restore defaults for this parts of '{config.filename}'")

    class LazyObserver(Observer):
        def __init__(self, timeout=DEFAULT_OBSERVER_TIMEOUT):
            super().__init__(timeout)
            self._sleeping = False

        def dispatch_events(self, *args, **kwargs):
            if not self._sleeping:
                super(ConfigManager.LazyObserver, self).dispatch_events(*args, **kwargs)

        def sleep(self):
            self._sleeping = True

        def wakeup(self):
            time.sleep(self.timeout)  # allow interim events to be queued
            self.event_queue.queue.clear()
            self._sleeping = False


class InteractionManager(AppElement):
    def setup(self):
        from system_hotkey import SystemHotkey
        hk = SystemHotkey()
        initial_hotkey = ('control', 'alt')
        special_key = 'shift'
        special_hotkey = (*initial_hotkey, special_key)
        hotkeys = {
            'kp_add': self.append_current_app,
            'kp_subtract': self.delete_current_app,
        }

        def make_callback(func, *args):
            return lambda e: func(*args)

        from inspect import signature
        for k, v in hotkeys.items():
            hk.register((*initial_hotkey, k), callback=make_callback(v))
            if signature(v).parameters:
                hk.register((*special_hotkey, k), callback=make_callback(v, True))

    def append_current_app(self, short_act=False):
        print('+')

    def delete_current_app(self, short_act=False):
        print('-')
