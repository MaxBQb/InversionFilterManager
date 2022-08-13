import ctypes

import win32con
import win32gui
import win32console


class Console:
    def __init__(self):
        self.handle: int = win32console.GetConsoleWindow()
        self._visible = True

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, value):
        self._visible = value
        win32gui.ShowWindow(
            self.handle,
            win32con.SW_SHOW if value else win32con.SW_HIDE
        )

    def hide(self):
        self.visible = False

    def show(self):
        self.visible = True


def is_admin():
    return ctypes.windll.shell32.IsUserAnAdmin()
