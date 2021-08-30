from dataclasses import dataclass
from typing import Callable, TypeVar
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


T = TypeVar('T')
OPTION_PATH = Callable[[UserSettings], T]
OPTION_CHANGE_HANDLER = Callable[[T], None]


class UserSettingsController:
    def __init__(self):
        self._syncer = ConfigSyncer("settings", UserSettings())
        self.filename = self._syncer.filename
        self._syncer.on_file_reloaded = self.on_settings_changed
        self._change_handlers: list[tuple[OPTION_PATH, OPTION_CHANGE_HANDLER]] = list()
        self._old_data = None

    def setup(self):
        self._syncer.start()
        self._syncer.preserve_on_update()

    @property
    def settings(self):
        return self._syncer.data

    def on_settings_changed(self):
        if self._old_data is None:
            self._old_data = self._syncer.data
            return

        for path, handler in self._change_handlers:
            new_value = path(self._syncer.data)
            if path(self._old_data) != new_value:
                handler(new_value)

        self._old_data = self._syncer.data

    def add_option_change_handler(self,
                                  path: OPTION_PATH,
                                  handler: OPTION_CHANGE_HANDLER):
        self._change_handlers.append((path, handler))


class ConfigSyncer(DataFileSyncer):
    JSON_DUMPER_KWARGS = dict(
        strip_privates=True,
        strip_properties=True
    )

    def _dump(self, stream):
        writer = CommentsWriter()
        super()._dump(writer.input_stream)
        writer.dump(stream, get_comments_holder(self._class))
