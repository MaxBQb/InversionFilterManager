import sys
from enum import Enum, auto


__version__ = "0.4.0"
__product_name__ = "InversionFilterManager"
__author__ = "MaxBQb"
__icon__ = "img/inversion_manager.ico"
__developer_mode__ = sys.argv[0].endswith(".py")
# N̲e̲v̲e̲r̲ change __instance_lock_key__, NEVER!
__instance_lock_key__ = 'InversionManager by MaxBQb app instance lock|7171670340b66dae2be937cca2b0f3de'


class IndirectDependency(Enum):
    SETTINGS_CONTROLLER = auto()
    CARRYON_BEFORE_UPDATE = auto()
