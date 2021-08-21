import os
import re
import subprocess


FILEBROWSER_PATH = os.path.join(os.getenv('WINDIR'), 'explorer.exe')


class MetaInitHook(type):
    """
    Run _cls_init classmethod each time
    when class or it's derivatives initialized
    (Class init != class instance init, which __init__ does
    """
    def __init__(cls, name, bases, dct):
        super().__init__(name, bases, dct)
        cls._cls_init()


class StrHolder(metaclass=MetaInitHook):
    """
    1) String constants are better then same string written twice
    2) But code like: some_constant = 'some_constant' annoying
    3) Write some_constant: str and let Python do it's work
    Inspired by dataclasses
    If someone will find better or existing solution => leave a comment plz

    Static use:
    class MyConstants(StrHolder):
        CONST_1: str
        CONST_2: str
        CONST_3: str

    You'll get:
    class MyConstants(StrHolder):
        CONST_1 = 'CONST_1'
        CONST_2 = 'CONST_2'
        CONST_3 = 'CONST_3'

    You may override _get_value:
    class ...:
        ...
        @staticmethod
        def _get_value(field_name: str) -> str:
            return field_name.capitalize().replace('_', ' ')

    Result:
    class MyConstants(StrHolder):
        CONST_1 = 'Const 1'
        CONST_2 = 'Const 2'
        CONST_3 = 'Const 3'

    You still can define constants by your own
    And each one will be available like so:

    MyConstants.CONST_1

    Dynamic use:
    class MyConstants(StrHolder):
        CONST_1: str
        CONST_2: str
        CONST_3: str

    instance = MyConstants(lambda x: x.replace('_', ' '))
    assert instance.CONST_2 == 'CONST 2'
    assert MyConstants.CONST_2 == 'CONST_2'

    Inheritance free use:
    class MyConstants:
        CONST_1: str
        CONST_2: str
        CONST_3: str

    StrHolder._field_names_to_values(MyConstants, lambda x: x.lower())
    assert MyConstants.CONST_3 == 'const_3'
    """
    def __init__(self, get_value):
        self._field_names_to_values(self, get_value)

    @staticmethod
    def _get_value(field_name: str) -> str:
        return field_name

    @classmethod
    def _cls_init(cls):
        cls._field_names_to_values(cls, cls._get_value)

    @staticmethod
    def _field_names_to_values(scope, get_value=lambda x: x):
        if not hasattr(scope, '__annotations__'):
            return
        for field in scope.__annotations__:
            if not field.startswith('_'):
                setattr(scope, field, get_value(field))


def ellipsis_trunc(text: str, width=12):
    if len(text) <= width or width < 1:
        return text
    return text[:width-1].rstrip() + "…"


def rename_key(container: dict, old_key, new_key, override=True) -> bool:
    if old_key not in container:
        return False

    if new_key in container and not override:
        return False

    value = container[old_key]
    del container[old_key]
    container[new_key] = value
    return True


def cycled_shift(start_pos: int, length: int, step=1):
    end_pos = (start_pos + step) % length
    return end_pos if end_pos >= 0 else end_pos + length


def max_len(iterable):
    return len(max(iterable, key=len))


def change_escape(text: str, escape: bool):
    if escape:
        return re.escape(text)
    return re.sub(r'\\([^\\]+)', r'\g<1>', text)


def alternative_path(path: str):
    from os.path import altsep, split
    return altsep.join(split(path))


def explore(path):
    if os.path.exists(path):
        subprocess.run([FILEBROWSER_PATH, os.path.normpath(path)])


def public_fields(object):
    return (
        (k, v)
        for k, v in vars(object).items()
        if not k.startswith('_')
    )
