from asyncio import to_thread
import inject
from configobj import ConfigObj
from app_close import AppCloseManager
from auto_update import AutoUpdater
from interaction import InteractionManager
from realtime_data_sync import RulesFileManager
from utils import explore


class Tray:
    config = inject.attr(ConfigObj)
    rules_file_manager = inject.attr(RulesFileManager)
    im = inject.attr(InteractionManager)
    updater = inject.attr(AutoUpdater)
    close_manager = inject.attr(AppCloseManager)

    def __init__(self):
        self.tray = None

    def setup(self):
        self.close_manager.add_exit_handler(self.close)

    def run(self):
        from _meta import __product_name__
        from pystray import Icon
        from PIL import Image
        self.tray = Icon(
            __product_name__,
            Image.open("img/inversion_manager.ico"),
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
        from pystray import Menu, MenuItem
        import _meta as app

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
                ref('Open'),
                Menu(
                    MenuItem(ref('Work directory'),
                             _open(".")),
                    MenuItem(ref('Config file'),
                             _open(self.config.filename)),
                    MenuItem(ref('Inversion rules file'),
                             _open(self.rules_file_manager.filename))
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