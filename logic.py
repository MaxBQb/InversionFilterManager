import asyncio
from pathlib import Path
from asyncio import create_task, to_thread
from configobj import ConfigObj
from active_window_checker import FilterStateController
from interaction import InteractionManager
from inversion_rules import InversionRulesController
from realtime_data_sync import ConfigFileManager, RulesFileManager
from auto_update import AutoUpdater
from main_thread_loop import MainExecutor
from app_close import AppCloseManager
from tray import Tray
import inject


class App:
    updater = inject.attr(AutoUpdater)
    state_controller = inject.attr(FilterStateController)
    interaction_manager = inject.attr(InteractionManager)
    config = inject.attr(ConfigObj)
    inversion_rules_file_manager = inject.attr(RulesFileManager)
    main_executor = inject.attr(MainExecutor)
    close_manager = inject.attr(AppCloseManager)
    tray = inject.attr(Tray)

    def setup(self):
        self.close_manager.setup()
        self.updater.on_update_applied = self.handle_update
        self.interaction_manager.setup()
        self.tray.setup()

    async def run(self):
        from active_window_checker import listen_switch_events

        tasks = []
        tasks.append(create_task(to_thread(
            listen_switch_events,
            self.state_controller.on_active_window_switched
        )))

        tasks.append(create_task(
            self.tray.run_async()
        ))

        tasks.append(create_task(
            self.main_executor.run_loop()
        ))

        self.updater.run_check_loop()

        print("I'm async")
        try:
            await asyncio.gather(*tasks)
        except asyncio.exceptions.CancelledError:
            pass
        print("Bye")

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


def configure(binder: inject.Binder):
    # Couple of components
    # Handled at runtime
    config_manager = ConfigFileManager("config")
    binder.bind(ConfigObj, config_manager.config)

    inversion_rules = InversionRulesController()
    inversion_rules_file_manager = RulesFileManager("inversion", inversion_rules)
    binder.bind(InversionRulesController, inversion_rules)
    binder.bind(RulesFileManager, inversion_rules_file_manager)


inject.configure(configure)
