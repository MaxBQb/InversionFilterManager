from distutils.core import setup
import py2exe
import codecs
import os.path


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


setup(console=['main.py'],
      name="InversionFilterManager",
      version=get_version("./_meta.py"),
      description="Inverts colors when you opens blinding white windows",
      data_files=[('.', ["config_description.ini"])]
      )