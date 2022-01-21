from ctypes import *
import inject
from app_close import AppCloseManager
from main_thread_loop import execute_in_main_thread


magnification_api = CDLL('magnification.dll')

# declare types
PMAGCOLOREFFECT = c_float * 25
MAGCOLOREFFECT = POINTER(PMAGCOLOREFFECT)

magnification_api.MagInitialize.restype = c_bool

magnification_api.MagUninitialize.restype = c_bool

magnification_api.MagSetFullscreenColorEffect.restype = c_bool
magnification_api.MagSetFullscreenColorEffect.argtypes = (MAGCOLOREFFECT,)


class ColorFilter:
    close_manager = inject.attr(AppCloseManager)

    _MATRIX_INVERSION = (PMAGCOLOREFFECT)(
        -1, 0, 0, 0, 0,
        0, -1, 0, 0, 0,
        0, 0, -1, 0, 0,
        0, 0, 0, 1, 0,
        1, 1, 1, 0, 1
    )

    _MATRIX_NONE = (PMAGCOLOREFFECT)(
        1, 0, 0, 0, 0,
        0, 1, 0, 0, 0,
        0, 0, 1, 0, 0,
        0, 0, 0, 1, 0,
        0, 0, 0, 0, 1
    )

    def __init__(self):
        self._is_active = False

    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, value: bool):
        if not isinstance(value, bool)\
           or self._is_active == value:
            return
        self._is_active = value
        self._set_filter_state(value)

    @execute_in_main_thread()
    def _set_filter_state(self, value: bool):
        matrix = (
            self._MATRIX_INVERSION
            if value else
            self._MATRIX_NONE
        )
        magnification_api.MagSetFullscreenColorEffect(matrix)

    def setup(self):
        magnification_api.MagInitialize()
        self.close_manager.add_exit_handler(
            magnification_api.MagUninitialize
        )
