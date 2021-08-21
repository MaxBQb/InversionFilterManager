from keyboard import press_and_release as hotkey
from winregal import RegKey


def is_active():
    with RegKey(r"HKEY_CURRENT_USER\Software\Microsoft\ColorFiltering") as key:
        return bool(key.get_value("Active").data)


def set_active(value):
    if value != is_active():
        toggle()


def toggle():
    hotkey("ctrl+win", do_release=False)
    hotkey(46)
    hotkey("ctrl+win", do_press=False)
