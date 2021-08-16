import color_filter
from keyboard import add_hotkey
from asyncio import create_task, to_thread
from configobj import ConfigObj
from active_window_checker import WindowInfo
from inversion_rules import InversionRulesController
from realtime_data_sync import ConfigFileManager, RulesFileManager
import inject


class App:
    def __init__(self):
        self.config_manager = ConfigFileManager("config")
        self.config = self.config_manager.config
        self.inversion_rules = InversionRulesController()
        self.inversion_rules_file_manager = RulesFileManager("inversion", self.inversion_rules)
        self.state_controller = FilterStateController()
        self.interaction_manager = InteractionManager()
        inject.configure(self.configure)

    async def run(self):
        from asyncio import gather
        from active_window_checker import listen_switch_events
        from auto_update import check_for_updates
        tasks = []
        if self.config["update"]["check_for_updates"]:
            tasks.append(create_task(check_for_updates(
                self.handle_update,
                self.config["update"]["ask_before_update"]
            )))
        tasks.append(create_task(to_thread(
            listen_switch_events,
            self.state_controller.on_active_window_switched
        )))
        self.interaction_manager.setup()
        tasks.append(create_task(
            self.interaction_manager.run_tray()
        ))
        print("I'm async")
        await gather(*tasks)

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
        binder.bind(RulesFileManager, self.inversion_rules_file_manager)
        binder.bind(FilterStateController, self.state_controller)
        binder.bind(InteractionManager, self.interaction_manager)


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

    def __init__(self):
        from gui import Tray
        self.tray = Tray()

    def setup(self):
        initial_hotkey = 'ctrl+alt+'

        hotkeys = {
            'plus': self.append_current_app,
            'subtract': self.delete_current_app,
        }

        for k, v in hotkeys.items():
            add_hotkey(initial_hotkey+k, v)

    async def run_tray(self):
        try:
            await to_thread(self.tray.run)
        finally:
            self.tray.close()

    def append_current_app(self, winfo: WindowInfo = None):
        from gui import RuleCreationWindow
        winfo = winfo or self.state_controller.last_active_window
        if not winfo:
            return
        rule, name = RuleCreationWindow(winfo).run()
        if name is not None and rule:
            self.rules_controller.add_rule(name, rule)

    def delete_current_app(self, winfo: WindowInfo = None):
        from gui import RuleRemovingWindow
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
