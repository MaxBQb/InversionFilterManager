import pyautogui as gui
import color_filter
from keyboard import add_hotkey
from file_tracker import FileTracker
from configobj import ConfigObj
from asyncio import create_task
import jsons
import yaml
from rules import RulesController
from apps_rules import AppsRulesController
from textwrap import shorten
from functools import partial

shorten = partial(shorten, width=60, placeholder="...")

class App:
    def __init__(self):
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


class ConfigFileManager(FileTracker):
    def __init__(self, name: str):
        self.config = ConfigObj(infile=name + ".ini",
                                configspec=name + "_description.ini",
                                create_empty=True,
                                write_empty_values=True)
        super().__init__(self.config.filename)

    def load_file(self):
        self.invalidate_config()

    def reload_file(self):
        self.config.reload()
        with self.observer.overlook():
            print(("Changes for '{}' applied"
                   if self.invalidate_config() else
                   "Changes for '{}' fixed & applied").format(self.config.filename))

    def invalidate_config(self):
        from validate import Validator
        validator = Validator()
        test = self.config.validate(validator,
                                    copy=True,
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
        self.config.validate(validator, copy=True)  # restore defaults as real values

    def invalidate_parts(self, validation_response: dict):
        from configobj import flatten_errors
        for sections, key, error in flatten_errors(self.config, validation_response):
            if not error:
                error = "missing"
            pointer = self.config
            for section in sections:
                pointer = pointer[section]
            print('.'.join(sections + [key]) + ":", error)
            pointer.restore_default(key)
            pointer[key] = pointer[key]  # current = default


class RulesFileManager(FileTracker):
    def __init__(self, name: str, rules_controller: RulesController):
        self.rules = None
        self.rules_controller = rules_controller
        self.rules_controller.on_modified = self.save_rules
        super().__init__(name + "_rules.yaml")

    def load_file(self):
        try:
            with self.observer.overlook():
                with open(self.filename) as f:
                    self.rules = yaml.safe_load(f)
            if self.rules is None:
                self.rules = {}
            for key in self.rules:
                self.rules[key] = jsons.load(self.rules[key],
                                             self.rules_controller.rule_type)
            self.dump_file()
        except FileNotFoundError:
            self.rules = {}
            with open(self.filename, "w"):
                pass

    def save_rules(self):
        self.rules = self.rules_controller.rules
        self.dump_file()

    def dump_file(self):
        with self.observer.overlook():
            with open(self.filename, "w") as f:
                yaml.dump(jsons.dump(self.rules,
                                     strip_properties=True,
                                     strip_nulls=True), f)

    def on_file_loaded(self):
        self.rules_controller.load(self.rules)

    def on_file_reloaded(self):
        print(f"Changes for '{self.filename}' applied")


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

    def append_current_app(self, short_act=False):
        winfo = self.app.state_controller.last_active_window
        if not self.confirm(f"Do you want to add '{winfo.title}' to inversion rules?\n(Path: '{winfo.path}')"):
            return

        name = self.prompt("Give name for your rule:", winfo.name.strip(".exe").title())
        rule = {}

        from apps_rules import AppRule, Text
        if not short_act:
            rule['path'] = Text(
                self.prompt("Use this path:", winfo.path),
                self.confirm(f"Do you want to use regex matching for path?\n(Default = no)")
            )

        if short_act or self.confirm(f"Do you want to add '{winfo.title}' by it's title?"):
            rule['title'] = Text(
                self.prompt("Use this title to check:", winfo.title),
                self.confirm(f"Do you want to use regex matching for title?\n(Default = no)")
            )
        self.app.apps_rules.add_rule(name, AppRule(**rule))

    def delete_current_app(self):
        winfo = self.app.state_controller.last_active_window
        if not self.app.apps_rules.check(winfo):
            return

        if not self.confirm(f"Do you want to remove '{winfo.title}' from inversion rules?\n(Path: '{winfo.path}')"):
            return

        rules = list(self.app.apps_rules.filter_rules(winfo))

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

