import pyautogui as gui
import color_filter
from keyboard import add_hotkey
from asyncio import create_task
from apps_rules import AppsRulesController
from textwrap import shorten
from functools import partial
from apps_rules import AppRule

shorten = partial(shorten, width=60, placeholder="...")


class App:
    def __init__(self):
        from realtime_data_sync import ConfigFileManager, RulesFileManager
        gui.FAILSAFE = False
        self.state_controller = FilterStateController(self)
        self.interaction_manager = InteractionManager(self)
        self.config_manager = ConfigFileManager("config")
        self.config = self.config_manager.config
        self.apps_rules = AppsRulesController()
        self.apps_rules_file_manager = RulesFileManager("apps", self.apps_rules)

    def run(self):
        from active_window_checker import listen_switch_events
        from auto_update import check_for_updates
        if self.config["update"]["check_for_updates"]:
            create_task(check_for_updates(self.handle_update,
                                          self.config["update"]["ask_before_update"]))
        create_task(listen_switch_events(
            self.state_controller.on_active_window_switched
        ))
        self.interaction_manager.setup()

    def handle_update(self, new_path, current_path, backup_filename):
        try:
            from shutil import copyfile
            from os import path

            copy_list = [
                self.config.filename,
                self.apps_rules_file_manager.filename
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


class AppElement:
    def __init__(self, app: App):
        self.app = app


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
        color_filter.set_active(self.app.apps_rules.check(winfo))


class InteractionManager(AppElement):
    def setup(self):
        initial_hotkey = 'ctrl+alt+'
        special_hotkey = initial_hotkey + 'shift+'
        hotkeys = {
            'plus': self.append_current_app,
            'subtract': self.delete_current_app,
        }

        from inspect import signature
        for k, v in hotkeys.items():
            if signature(v).parameters:
                add_hotkey(special_hotkey+k, v, args=(True,))
            add_hotkey(initial_hotkey+k, v)

    def append_current_app(self):
        from gui.select_window import select_window
        winfo = self.app.state_controller.last_active_window
        res = select_window(winfo)
        if not res:
            return
        self.app.apps_rules.add_rule(res[1], AppRule(**res[0]))
        return

    def delete_current_app(self):
        from gui.select_rules import select_rules
        winfo = self.app.state_controller.last_active_window
        if not self.app.apps_rules.check(winfo):
            return

        rules = list(self.app.apps_rules.filter_rules(winfo))
        select_rules(rules)
        return
        if not rules:
            gui.alert("Something went wrong, none of the rules matches this window!\n"
                      "But the last check says it does...\n"
                      "Please inform author of the script about this occasion :(")
            return
        elif len(rules) == 1:
            if not self.confirm(f"One rule found: '{shorten(rules[0])}', remove it?"):
                return
        else:
            if not self.confirm(f"Couple of rules found: [{shorten(', '.join(rules[:20]))}], remove them all?"):
                if not self.confirm(f"Remove selected only?"):
                    return

                rules = [rule for rule in rules
                         if self.confirm(f"Remove '{shorten(rule)}'?")]
        self.app.apps_rules.remove_rules(rules)

    @staticmethod
    def confirm(text) -> bool:
        from pymsgbox import OK_TEXT
        return OK_TEXT == gui.confirm(text)

    @staticmethod
    def prompt(text, default=""):
        result = gui.prompt(text=text, default=default)
        return result if result is not None else default

