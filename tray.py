from asyncio import to_thread
import inject
import win32gui
from win32con import SW_HIDE, SW_SHOW
import win32console
from PIL import Image
from pystray import Menu, MenuItem, Icon
import _meta as app
from app_close import AppCloseManager
from auto_update import AutoUpdater
from interaction import InteractionManager
from inversion_rules import InversionRulesController
from settings import UserSettingsController
from utils import explore


def make_toggle(out_func=None, default_value=False):
    def decorator(func):
        def wrapper(self):
            value = [default_value]

            def get_value(item):
                return value[0]

            def toggle():
                value[0] ^= True
                func(self, value[0])

            return toggle, get_value
        return wrapper
    if out_func:
        return decorator(out_func)
    return decorator


class Tray:
    settings_controller = inject.attr(UserSettingsController)
    inversion_rules = inject.attr(InversionRulesController)
    im = inject.attr(InteractionManager)
    updater = inject.attr(AutoUpdater)
    close_manager = inject.attr(AppCloseManager)

    def __init__(self):
        self.tray = None
        self.console_hwnd: int = None
        self.console_shown = False

    def setup(self):
        self.close_manager.add_exit_handler(self.close)
        self.console_hwnd = win32console.GetConsoleWindow()
        self.close_manager.add_exit_handler(lambda: win32gui.ShowWindow(
            self.console_hwnd,
            SW_SHOW
        ))
        win32gui.ShowWindow(self.console_hwnd, SW_HIDE)

    def run(self):
        self.tray = Icon(
            app.__product_name__,
            Image.open(app.__icon__),
            menu=self.build_menu()
        )
        self.tray.run()

    async def run_async(self):
        try:
            await to_thread(self.run)
        finally:
            self.tray.close()

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

        def ref(text: str):
            """
            Make first letter underscored, also
            mark this letter as shortcut for system tray,
            so you may press this letter on keyboard
            to select corresponding menu item
            """
            return f'&{text[0]}\u0332{text[1:]}'

        im = self.im
        return Menu(
            MenuItem(
                f'{app.__product_name__} v{app.__version__}',
                None, enabled=False),
            Menu.SEPARATOR,
            MenuItem(
                ref("Show console"),
                *self.toggle_console()
            ),
            Menu.SEPARATOR,
            MenuItem(
                ref('Open'),
                Menu(
                    MenuItem(ref('Work directory'),
                             _open(".")),
                    MenuItem(ref('Settings file'),
                             _open(self.settings_controller.filename)),
                    MenuItem(ref('Inversion rules file'),
                             _open(self.inversion_rules.filename))
                )
            ),
            MenuItem(
                'Re' + ref('load from disk'),
                Menu(
                    MenuItem(ref('Settings file'),
                             callback(self.settings_controller.load)),
                    MenuItem(ref('Inversion rules file'),
                             callback(self.settings_controller.load)),
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

    @make_toggle
    def toggle_console(self, value):
        win32gui.ShowWindow(
            self.console_hwnd,
            SW_SHOW if value else SW_HIDE
        )
