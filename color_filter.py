import inject
from app_close import AppCloseManager
from main_thread_loop import execute_in_main_thread
import win_magnification as mag


class ColorFilter:
    close_manager = inject.attr(AppCloseManager)
    inversion_percentage = 0.95
    _MATRIX_INVERSION = mag.effects.inversion(inversion_percentage)

    def __init__(self):
        self.api: mag.WinMagnificationAPI = None

    @property
    def is_active(self):
        return self.api.fullscreen.color_effect != self.api.fullscreen.color_effect.default

    @is_active.setter
    def is_active(self, value: bool):
        if not isinstance(value, bool):
            return
        self._set_filter_state(value)

    @execute_in_main_thread()
    def _set_filter_state(self, value: bool):
        if value:
            self.api.fullscreen.color_effect.raw = self._MATRIX_INVERSION
        else:
            self.api.fullscreen.color_effect.reset()

    def setup(self):
        self.api = mag.WinMagnificationAPI()
        self.close_manager.add_exit_handler(
            self.api.dispose
        )
