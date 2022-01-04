from distutils.core import setup
from glob import glob
import py2exe
import _meta as app


# py2exe says 'site' package unavailable for windows => useless
# but somewhat I've got import error without next line
py2exe.hooks.windows_excludes.remove("site")


setup(console=[dict(
        script='main.py',
        icon_resources=[(0, app.__icon__)],
      )],
      name=app.__product_name__,
      version=app.__version__,
      author=app.__author__,
      description="Inverts colors when you opens blinding white windows",
      data_files=[('.', ["update.bat"]),
                  ('./img', glob('img/*'))],
      options=dict(
          py2exe=dict(
              includes='pystray._win32'
          )
      ))
