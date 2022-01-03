import asyncio
import os
import inject
from active_window_checker import FilterStateController
from app_close import AppCloseManager
from auto_update import AutoUpdater
from _meta import IndirectDependency, APP_DIR
from interaction import InteractionManager
from inversion_rules import InversionRulesController
from main_thread_loop import MainExecutor
from settings import UserSettings, UserSettingsController
from tray.tray import Tray


class AppStartManager:
    updater = inject.attr(AutoUpdater)
    state_controller = inject.attr(FilterStateController)
    interaction_manager = inject.attr(InteractionManager)
    settings_controller = inject.attr(UserSettingsController)
    inversion_rules = inject.attr(InversionRulesController)
    main_executor = inject.attr(MainExecutor)
    close_manager = inject.attr(AppCloseManager)
    tray = inject.attr(Tray)

    def setup(self):
        os.chdir(APP_DIR)
        self.settings_controller.setup()
        self.inversion_rules.setup()
        self.state_controller.setup()
        self.close_manager.setup()
        self.interaction_manager.setup()
        self.tray.setup()

    async def run(self):
        self.updater.run_check_loop()

        print("I'm async")
        try:
            await asyncio.gather(
                self.state_controller.run(),
                self.tray.run_async(),
                self.main_executor.run_loop(),
            )
        except asyncio.exceptions.CancelledError:
            pass
        print("Bye")


def configure(binder: inject.Binder):
    # Couple of components
    # Handled at runtime
    settings_controller = UserSettingsController()
    binder.bind(IndirectDependency.SETTINGS_CONTROLLER, settings_controller)
    binder.bind(settings_controller.__class__, settings_controller)

    for field, class_ in UserSettings.__annotations__.items():
        binder.bind_to_provider(
            class_, lambda field=field: getattr(
                settings_controller.settings,
                field
            )
        )

    binder.bind_to_provider(IndirectDependency.CARRYON_BEFORE_UPDATE,
                            lambda: inject.instance(AutoUpdater).carryon)


inject.configure(configure)
