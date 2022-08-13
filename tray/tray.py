from asyncio import to_thread
from contextlib import closing

import inject
from PIL import Image
from pystray import Menu, MenuItem, Icon

import _meta as app
from active_window_checker import AppMode
from app_close import AppCloseManager
from auto_update import AutoUpdater
from color_filter import ColorFiltersListController
from interaction import InteractionManager
from inversion_rules import InversionRulesController
from settings import UserSettingsController, OPTION_PATH, OPTION_CHANGE_HANDLER, T
from tray.features import is_admin, Console
from tray.utils import ref, make_toggle, make_radiobutton
from utils import explore, app_abs_path, show_exceptions


class Tray:
    settings_controller = inject.attr(UserSettingsController)
    inversion_rules = inject.attr(InversionRulesController)
    color_filters_holder = inject.attr(ColorFiltersListController)
    im = inject.attr(InteractionManager)
    updater = inject.attr(AutoUpdater)
    close_manager = inject.attr(AppCloseManager)
    console = inject.attr(Console)

    def __init__(self):
        self.tray = None

    def setup(self):
        self.close_manager.add_exit_handler(self.close)
        self.close_manager.add_exit_handler(self.console.show)
        self.console.hide()

    @show_exceptions()
    def run(self):
        self.tray = Icon(
            app.__product_name__,
            Image.open(app_abs_path(app.__icon__)),
            menu=self.build_menu()
        )
        self.tray.run_detached()

    async def run_async(self):
        with closing(self):
            await to_thread(self.run)

    def close(self):
        if self.tray:
            self.tray.stop()

    def build_menu(self):
        def callback(func, *args, **kwargs):
            def _wrapper(*ignore):
                func(*args, **kwargs)
            return _wrapper

        def _open(path):
            return callback(explore, path)

        change_mode_menu, change_mode_setter = self.change_mode()

        self._link_with_settings(
            lambda settings: settings.win_tracker.mode,
            change_mode_setter
        )

        im = self.im
        return Menu(
            MenuItem(
                f'{app.__product_name__} v{app.__version__}'
                + (" (Admin)" if is_admin() else ""),
                None, enabled=False),
            Menu.SEPARATOR,
            MenuItem(
                ref("Show console"),
                *self.toggle_console()
            ),
            MenuItem(
                ref("Mode"),
                change_mode_menu
            ),
            Menu.SEPARATOR,
            MenuItem(
                ref('Open'),
                Menu(
                    MenuItem(ref('Work directory'),
                             _open(app.APP_DIR)),
                    MenuItem(ref('Settings file'),
                             _open(app_abs_path(
                                 self.settings_controller.filename
                             ))),
                    MenuItem(ref('Inversion rules file'),
                             _open(app_abs_path(
                                 self.inversion_rules.filename
                             ))),
                    MenuItem(ref('Color filters file'),
                             _open(app_abs_path(
                                 self.color_filters_holder.filename
                             ))),
                )
            ),
            MenuItem(
                'Re' + ref('load from disk'),
                Menu(
                    MenuItem(ref('Settings file'),
                             callback(self.settings_controller.load)),
                    MenuItem(ref('Inversion rules file'),
                             callback(self.inversion_rules.load)),
                    MenuItem(ref('Color filters file'),
                             callback(self.color_filters_holder.load)),
                )
            ),
            Menu.SEPARATOR,
            MenuItem(ref('Add app to inversion rules'),
                     callback(im.choose_window_to_make_rule)),
            MenuItem(ref('Remove app from inversion rules'),
                     callback(im.choose_window_to_remove_rules)),
            Menu.SEPARATOR,
            MenuItem(f'Check for {ref("updates")}',
                     callback(self.updater.check_for_updates)),
            Menu.SEPARATOR,
            MenuItem(ref('Exit'),
                     callback(self.close_manager.close)),
        )

    def _link_with_settings(self,
                            path: OPTION_PATH,
                            handler: OPTION_CHANGE_HANDLER,):
        def new_handler(value: T):
            handler(value)
            if self.tray:
                self.tray.update_menu()

        self.settings_controller.add_option_change_handler(
            path, new_handler, True
        )

    @make_toggle
    def toggle_console(self, value):
        self.console.visible = value

    @make_radiobutton({
        AppMode.DISABLE: ref("Ignore All"),
        AppMode.RULES: ref("According with rules"),
    }, AppMode.RULES)
    def change_mode(self, value: AppMode):
        self.settings_controller.settings.win_tracker.mode = value
        self.settings_controller.save()
