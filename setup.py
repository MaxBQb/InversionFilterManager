import codecs
import os.path
from distutils.core import setup
from functools import partial
from glob import glob
import py2exe


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_entry(rel_path, key):
    for line in read(rel_path).splitlines():
        if line.startswith(key):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError(f"Unable to find {key} string.")


get_meta = partial(get_entry, './_meta.py')

# py2exe says 'site' package unavailable for windows => useless
# but somewhat I've got import error without next line
py2exe.hooks.windows_excludes.remove("site")


def dirty_pystray_fix():
    from pystray import __path__ as tray_path, __package__ as tray_package
    tray_path = os.path.join(tray_path[0], "__init__.py")

    with open(tray_path, "r", encoding="utf-8") as f:
        data = f.readlines()

    if not data[0].startswith('__package__'):
        with open(tray_path, "w", encoding="utf-8") as f:
            f.writelines([f"__package__ = '{tray_package}'\n"] + data)


# Pystray can't find __package__ after py2exe'fication
# Okay.. if someone have clean solution, leave comment plz
dirty_pystray_fix()


setup(console=[dict(
        script='main.py',
        icon_resources=[(0, get_meta('__icon__'))],
      )],
      name=get_meta('__product_name__'),
      version=get_meta('__version__'),
      author=get_meta('__author__'),
      description="Inverts colors when you opens blinding white windows",
      data_files=[('.', ["config_description.ini", "update.bat"]),
                  ('./img', glob('img/*'))],
      options=dict(
          py2exe=dict(
              optimize=2,
              includes='pystray._win32'
          )
      ))
