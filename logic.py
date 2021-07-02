import time
import pyautogui as gui
from keyboard import press_and_release as hotkey, add_hotkey
from file_tracker import FileTracker
from winregal import RegKey
from configobj import ConfigObj
from asyncio import create_task


class App:
    def __init__(self):
        gui.FAILSAFE = False
        self.state_controller = FilterStateController(self)
        self.interaction_manager = InteractionManager(self)
        self.config_manager = ConfigManager("config")
        self.rules_manager = ConfigManager("rules")
        self.config = self.config_manager.config
        self.rules = self.rules_manager.config

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
        hotkey("ctrl+win+с")


class FilterStateController(AppElement):
    def on_active_window_switched(self,
                                  hWinEventHook,
                                  event,
                                  hwnd,
                                  idObject,
                                  idChild,
                                  dwEventThread,
                                  dwmsEventTime):
        from active_window_checker import get_window_info, eventTypes
        winfo = self.last_active_window = get_window_info(hwnd, idObject, dwEventThread)
        if self.app.config["display"]["show_events"]:
            print(winfo.path, eventTypes.get(event, hex(event)))
        InversionFilterController.set(winfo.name == "mspaint.exe")


class ConfigManager(FileTracker):
    def __init__(self, name: str, write_defaults=True):
        self.write_defaults = write_defaults
        self.config = ConfigObj(infile=name + ".ini",
                                configspec=name + "_description.ini",
                                create_empty=True,
                                write_empty_values=True)
        super().__init__(self.config.filename)

    def load_file(self):
        self.invalidate_config()

    def reload_file(self):
        self.config.reload()
        self.observer.sleep()
        print(("Changes for '{}' applied"
               if self.invalidate_config() else
               "Changes for '{}' fixed & applied").format(self.config.filename))
        self.observer.wakeup()

    def invalidate_config(self):
        from validate import Validator
        validator = Validator()
        test = self.config.validate(validator,
                                    copy=self.write_defaults,
                                    preserve_errors=True)
        check_failed = test is not True
        if test is False:
            print("Invalid configuration found.")
            self.invalidate_full(Validator())
            print(f"Restore defaults for '{self.config.filename}'")
        elif check_failed:
            print("Invalid configuration parts found.")
            self.invalidate_parts(test)
            print(f"Restore defaults for this parts of '{self.config.filename}'")
        self.config.initial_comment = ["Feel free to edit this config file"]
        self.config.write()
        return not check_failed

    def invalidate_full(self, validator):
        self.config.restore_defaults()
        self.config.validate(validator, copy=self.write_defaults)  # restore defaults as real values

    def invalidate_parts(self, test: dict):
        from configobj import flatten_errors
        for sections, key, error in flatten_errors(self.config, test):
            if not error:
                error = "missing"
            pointer = self.config
            for section in sections:
                pointer = pointer[section]
            print('.'.join(sections + [key]) + ":", error)
            pointer.restore_default(key)
            if self.write_defaults:
                pointer[key] = pointer[key]  # current = default


class InteractionManager(AppElement):
    def setup(self):
        initial_hotkey = 'ctrl+alt+'
        special_hotkey = initial_hotkey + 'shift+'
        hotkeys = {
            'plus': self.append_current_app,
            'minus': self.delete_current_app,
        }

        from inspect import signature
        for k, v in hotkeys.items():
            if signature(v).parameters:
                add_hotkey(special_hotkey+k, v, args=(True,))
            add_hotkey(initial_hotkey+k, v)

    def append_current_app(self, short_act=False):
        winfo = self.app.state_controller.last_active_window
        if not self.confirm(f"Do you want to add '{winfo.title}' to inversion rules?\n(Path: '{winfo.path}')"):
            return

        rules = self.app.rules
        apps = rules['Apps']
        name = self.prompt("Give name for your rule:", winfo.name.strip(".exe").title())
        app = {}

        if not short_act:
            app['path_regex'] = self.confirm(f"Do you want to use regex matching for path?\n(Default = no)")
            app['path'] = self.prompt("Use this path:", winfo.path)

        if short_act or self.confirm(f"Do you want to add '{winfo.title}' by it's title?"):
            app['title_regex'] = self.confirm(f"Do you want to use regex matching for title?\n(Default = no)")
            app['title'] = self.prompt("Use this title to check:", winfo.title)

        apps[name] = app
        rules.write()

    def delete_current_app(self, short_act=False):
        print('-')

    @staticmethod
    def confirm(text) -> bool:
        from pymsgbox import OK_TEXT
        return OK_TEXT == gui.confirm(text)

    @staticmethod
    def prompt(text, default=""):
        result = gui.prompt(text=text, default=default)
        return result if result is not None else default

