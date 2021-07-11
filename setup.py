from distutils.core import setup
import py2exe

setup(console=['main.py'],
      name="InversionFilterManager",
      version="0.0.2",
      description="Inverts colors when you opens blinding white windows",
      data_files=[('.', ["config_description.ini"])]
      )