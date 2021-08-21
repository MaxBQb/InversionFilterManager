import asyncio
from asyncio import create_task, to_thread
from pathlib import Path
import inject
from configobj import ConfigObj
from active_window_checker import FilterStateController
from app_close import AppCloseManager
from auto_update import AutoUpdater
from interaction import InteractionManager
from inversion_rules import InversionRulesController
from main_thread_loop import MainExecutor
from realtime_data_sync import ConfigFileManager, RulesFileManager
from tray import Tray


class AppStartManager:
    updater = inject.attr(AutoUpdater)
    state_controller = inject.attr(FilterStateController)
    interaction_manager = inject.attr(InteractionManager)
    config_file_manager = inject.attr(ConfigFileManager)
    config = inject.attr(ConfigObj)
    inversion_rules_file_manager = inject.attr(RulesFileManager)
    main_executor = inject.attr(MainExecutor)
    close_manager = inject.attr(AppCloseManager)
    tray = inject.attr(Tray)

    def setup(self):
        self.close_manager.setup()
        self.config_file_manager.setup()
        self.inversion_rules_file_manager.setup()
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


def configure(binder: inject.Binder):
    # Couple of components
    # Handled at runtime
    config_manager = ConfigFileManager("config")
    binder.bind(ConfigFileManager, config_manager)
    binder.bind(ConfigObj, config_manager.config)

    inversion_rules = InversionRulesController()
    inversion_rules_file_manager = RulesFileManager("inversion", inversion_rules)
    binder.bind(InversionRulesController, inversion_rules)
    binder.bind(RulesFileManager, inversion_rules_file_manager)


inject.configure(configure)
