from contextlib import suppress
from dataclasses import dataclass
from time import sleep
import inject
from keyboard import press_and_release as hotkey, call_later
from winregal import RegKey
from os import system
from commented_config import CommentsHolder


@dataclass
class ColorFilterSettings:
    """
    Set filter settings on startup
    """
    _comments_ = CommentsHolder()

    setup_filter_state: bool = True
    _comments_.add("""
       [{default!r}] Open settings and setup:
       Allow the shortcut key to toggle filter = Checked
       Filter type = Inverted [first]
    """, locals())

    close_settings: bool = True
    _comments_.add("""
       [{default!r}] Close settings after setup
    """, locals())


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
    if value is None:
        return

    if value != is_active():
        toggle()


def toggle():
    hotkey(('ctrl', 'win', 46))


@inject.autoparams()
def setup_color_filer_settings(settings: ColorFilterSettings):
    if not settings.setup_filter_state:
        return

    hotkey_enabled = is_hotkey_enabled()

    if hotkey_enabled and get_filter_type() == 1:
        return

    was_active = is_active()
    system("start ms-settings:easeofaccess-colorfilter")
    sleep(1)
    # Windows has bug, when opening easeofaccess-colorfilter
    # while this window is already opened
    # filter will always set to Grayscale
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

    if settings.close_settings:
        hotkey("Alt + F4")
