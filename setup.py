import os.path
from distutils.core import setup
from glob import glob
import py2exe
import _meta as app


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
        icon_resources=[(0, app.__icon__)],
      )],
      name=app.__product_name__,
      version=app.__version__,
      author=app.__author__,
      description="Inverts colors when you opens blinding white windows",
      data_files=[('.', ["config_description.ini", "update.bat"]),
                  ('./img', glob('img/*'))],
      options=dict(
          py2exe=dict(
              optimize=2,
              includes='pystray._win32'
          )
      ))
