from distutils.core import setup
import py2exe
import codecs
import os.path
from functools import partial


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

setup(console=['main.py'],
      name=get_meta('__product_name__'),
      version=get_meta('__version__'),
      author=get_meta('__author__'),
      description="Inverts colors when you opens blinding white windows",
      data_files=[('.', ["config_description.ini", "update.bat"])],
      )
