from typing import Hashable

from pystray import Menu, MenuItem


def ref(text: str):
    """
    Make first letter underscored, also
    mark this letter as shortcut for system tray,
    so you may press this letter on keyboard
    to select corresponding menu item
    """
    return f'&{text[0]}\u0332{text[1:]}'


def make_toggle(setter=None, default_value=False):
    value = [default_value]

    def get_value(item):
        return value[0]

    def toggle():
        value[0] ^= True
        setter(value[0])

    return toggle, get_value


def make_radiobutton(values: dict[Hashable, str],
                     default_value=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            value_ref = [default_value or next(iter(values))]

            def change(value):
                value_ref[0] = value
                func(*args, value=value_ref[0], **kwargs)

            return Menu(*[
                MenuItem(
                    name,
                    lambda *_, value=value: change(value),
                    lambda *_, value=value: value_ref[0] == value,
                    True
                ) for value, name in values.items()
            ]), change
        return wrapper
    return decorator
