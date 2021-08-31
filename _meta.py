import sys
from enum import Enum, auto


__version__ = "0.4.0"
__product_name__ = "InversionFilterManager"
__author__ = "MaxBQb"
__icon__ = "img/inversion_manager.ico"
__developer_mode__ = sys.argv[0].endswith(".py")


class IndirectDependency(Enum):
    SETTINGS_CONTROLLER = auto()
    CARRYON_BEFORE_UPDATE = auto()
