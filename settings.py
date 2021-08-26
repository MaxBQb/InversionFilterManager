from dataclasses import dataclass
from active_window_checker import WinTrackerSettings
from auto_update import AutoUpdateSettings
from commented_config import CommentsHolder


@dataclass
class UserSettings:
    _comments_ = CommentsHolder()

    win_tracker: WinTrackerSettings = WinTrackerSettings()
    _comments_.add(None, locals(), True)

    auto_update: AutoUpdateSettings = AutoUpdateSettings()
    _comments_.add(None, locals())
