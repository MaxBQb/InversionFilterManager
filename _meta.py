from enum import Enum, auto


__version__ = "0.4.0"
__product_name__ = "InversionFilterManager"
__author__ = "MaxBQb"
__icon__ = "img/inversion_manager.ico"


class IndirectDependency(Enum):
    SETTINGS_CONTROLLER = auto()
