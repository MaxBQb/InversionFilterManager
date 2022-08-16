from distutils.core import setup
from glob import glob

# noinspection PyUnresolvedReferences,PyPackageRequirements
import py2exe  # type: ignore

import _meta as app

with open('manifest.xml') as f:
    manifest = f.read()

setup(console=[dict(
        script='main.py',
        icon_resources=[(0, app.__icon__)],
        other_resources=[(24, 1, manifest)],
      )],
      name=app.__product_name__,
      version=app.__version__,
      author=app.__author__,
      description="Inverts colors when you open blindingly white windows",
      data_files=[('.', ["update.bat", "StartupTaskTemplate.xml"]),
                  ('./img', glob('img/*'))],
      options=dict(
          py2exe=dict(
              includes='pystray._win32'
          )
      ))
