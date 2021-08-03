import pyautogui as gui
import color_filter
from keyboard import add_hotkey
from asyncio import create_task
from configobj import ConfigObj
from apps_rules import AppsRulesController
from apps_rules import AppRule
import inject


class App:
    def __init__(self):
        from realtime_data_sync import ConfigFileManager, RulesFileManager
        gui.FAILSAFE = False
        self.config_manager = ConfigFileManager("config")
        self.config = self.config_manager.config
        self.apps_rules = AppsRulesController()
        self.apps_rules_file_manager = RulesFileManager("apps", self.apps_rules)
        self.state_controller = FilterStateController()
        self.interaction_manager = InteractionManager()
        inject.configure(self.configure)

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

    def configure(self, binder: inject.Binder):
        binder.bind(ConfigObj, self.config)
        binder.bind(AppsRulesController, self.apps_rules)
        binder.bind(FilterStateController, self.state_controller)
        binder.bind(InteractionManager, self.interaction_manager)


class FilterStateController:
    config = inject.attr(ConfigObj)
    rules = inject.attr(AppsRulesController)

    def __init__(self):
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
        winfo = self.last_active_window = get_window_info(hwnd, idObject, dwEventThread)
        if self.config["display"]["show_events"]:
            print(winfo.path, eventTypes.get(event, hex(event)))
        color_filter.set_active(self.rules.check(winfo))


class InteractionManager:
    state_controller = inject.attr(FilterStateController)
    rules = inject.attr(AppsRulesController)

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
        from gui import RuleCreationWindow
        winfo = self.state_controller.last_active_window
        raw_rule, name = RuleCreationWindow(winfo).run()
        if name is None or not raw_rule:
            return
        self.rules.add_rule(name, AppRule(**raw_rule))
        return

    def delete_current_app(self):
        from gui import RuleRemovingWindow
        winfo = self.state_controller.last_active_window
        if not self.rules.check(winfo):
            return

        rules = RuleRemovingWindow(list(
            self.rules.filter_rules(winfo)
        )).run()
        if not rules:
            return
        self.rules.remove_rules(rules)

    @staticmethod
    def confirm(text) -> bool:
        from pymsgbox import OK_TEXT
        return OK_TEXT == gui.confirm(text)

    @staticmethod
    def prompt(text, default=""):
        result = gui.prompt(text=text, default=default)
        return result if result is not None else default

