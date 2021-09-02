from contextlib import suppress
from time import sleep
from keyboard import press_and_release as hotkey
from winregal import RegKey
from os import system


def _get_filter_info(value: str):
    with suppress(FileNotFoundError):
        with RegKey(r"HKEY_CURRENT_USER\Software\Microsoft\ColorFiltering") as key:
            return key.get_value(value).data


def is_active():
    return bool(_get_filter_info("Active"))


def is_hotkey_enabled():
    return bool(_get_filter_info("HotkeyEnabled"))


def get_filter_type():
    return _get_filter_info("FilterType") or 2  # Grayscale by default


def set_active(value):
    if value != is_active():
        toggle()


def toggle():
    hotkey("ctrl+win", do_release=False)
    hotkey(46)
    hotkey("ctrl+win", do_press=False)


def setup_color_filer_settings():
    hotkey_enabled = is_hotkey_enabled()

    if hotkey_enabled and get_filter_type() == 1:
        return

    was_active = is_active()
    system("start ms-settings:easeofaccess-colorfilter")
    sleep(1)
    # Windows has bug, when opening easeofaccess-colorfilter
    # while this window is already opened
    # filter will always set to Gray
    # So you must check which filter selected twice :)

    options = (was_active, hotkey_enabled, get_filter_type() == 1)
    for skip_option in options:
        if not skip_option:
            hotkey("Space")
        hotkey("Tab")

    if not was_active:
        for i in range(len(options)):
            hotkey("Shift + Tab")
        hotkey("Space")

    hotkey("Alt + F4")
