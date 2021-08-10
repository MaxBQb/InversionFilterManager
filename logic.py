import color_filter
from keyboard import add_hotkey
from asyncio import create_task
from configobj import ConfigObj
from inversion_rules import InversionRule, InversionRulesController
import inject


class App:
    def __init__(self):
        from realtime_data_sync import ConfigFileManager, RulesFileManager
        self.config_manager = ConfigFileManager("config")
        self.config = self.config_manager.config
        self.inversion_rules = InversionRulesController()
        self.inversion_rules_file_manager = RulesFileManager("inversion", self.inversion_rules)
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
        binder.bind(ConfigObj, self.config)
        binder.bind(InversionRulesController, self.inversion_rules)
        binder.bind(FilterStateController, self.state_controller)
        binder.bind(InteractionManager, self.interaction_manager)


class FilterStateController:
    config = inject.attr(ConfigObj)
    rules = inject.attr(InversionRulesController)

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
        if idObject != 0:
            return
        winfo = self.last_active_window = get_window_info(hwnd)
        if self.config["display"]["show_events"]:
            print(winfo.path, eventTypes.get(event, hex(event)))
        color_filter.set_active(self.rules.is_inversion_required(winfo))


class InteractionManager:
    state_controller = inject.attr(FilterStateController)
    rules_controller = inject.attr(InversionRulesController)

    def setup(self):
        initial_hotkey = 'ctrl+alt+'

        hotkeys = {
            'plus': self.append_current_app,
            'subtract': self.delete_current_app,
        }

        for k, v in hotkeys.items():
            add_hotkey(initial_hotkey+k, v)

    def append_current_app(self):
        from gui import RuleCreationWindow
        winfo = self.state_controller.last_active_window
        rule, name = RuleCreationWindow(winfo).run()
        if name is None or not rule:
            return
        self.rules_controller.add_rule(name, rule)
        return

    def delete_current_app(self):
        from gui import RuleRemovingWindow
        winfo = self.state_controller.last_active_window
        if not self.rules_controller.is_inversion_required(winfo):
            return

        rules = RuleRemovingWindow(list(
            self.rules_controller.get_active_rules(winfo, self.rules_controller.rules)
        )).run()
        if not rules:
            return
        self.rules_controller.remove_rules(rules)
