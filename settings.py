from dataclasses import dataclass
from active_window_checker import WinTrackerSettings
from auto_update import AutoUpdateSettings
from commented_config import CommentsHolder, CommentsWriter, get_comments_holder
from file_tracker import DataFileSyncer


@dataclass
class UserSettings:
    _comments_ = CommentsHolder()

    win_tracker: WinTrackerSettings = WinTrackerSettings()
    _comments_.add(None, locals(), True)

    auto_update: AutoUpdateSettings = AutoUpdateSettings()
    _comments_.add(None, locals())


class ConfigSyncer(DataFileSyncer):
    JSON_DUMPER_KWARGS = dict(
        strip_privates=True,
        strip_properties=True
    )

    def _dump(self, stream):
        writer = CommentsWriter()
        super()._dump(writer.input_stream)
        writer.dump(stream, get_comments_holder(self._class))
