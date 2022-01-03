from copy import deepcopy
from dataclasses import dataclass
from typing import Callable, TypeVar, TextIO
from active_window_checker import WinTrackerSettings
from auto_update import AutoUpdateSettings
from color_filter import ColorFilterSettings
from commented_config import CommentsHolder, CommentsWriter, get_comments_holder
from file_tracker import DataFileSyncer, Syncable


@dataclass
class UserSettings:
    _comments_ = CommentsHolder()

    win_tracker: WinTrackerSettings = WinTrackerSettings()
    _comments_.add(None, locals(), True)

    color_filter: ColorFilterSettings = ColorFilterSettings()
    _comments_.add(None, locals(), True)

    auto_update: AutoUpdateSettings = AutoUpdateSettings()
    _comments_.add(None, locals())


T = TypeVar('T')
OPTION_PATH = Callable[[UserSettings], T]
OPTION_CHANGE_HANDLER = Callable[[T], None]


class UserSettingsController(Syncable):
    def __init__(self):
        super().__init__(ConfigSyncer("settings", UserSettings()))
        self._syncer.on_file_reloaded = self.on_settings_changed
        self._change_handlers: list[tuple[OPTION_PATH, OPTION_CHANGE_HANDLER]] = list()
        self._old_data = deepcopy(self.settings)
        self._loaded_data = deepcopy(self.settings)

    def setup(self):
        self._syncer.start()
        self._syncer.preserve_on_update()

    @property
    def settings(self) -> UserSettings:
        return self._syncer.data

    def on_settings_changed(self):
        self._loaded_data = deepcopy(self.settings)
        for path, handler in self._change_handlers:
            new_value = path(self.settings)
            if path(self._old_data) != new_value:
                handler(new_value)
        self._old_data = deepcopy(self.settings)

    def save(self):
        if self._loaded_data != self.settings:
            super().save()
            self._loaded_data = deepcopy(self.settings)
            self._old_data = deepcopy(self.settings)

    def add_option_change_handler(self,
                                  path: OPTION_PATH,
                                  handler: OPTION_CHANGE_HANDLER,
                                  initial=False):
        self._change_handlers.append((path, handler))
        if initial:
            handler(path(self._syncer.data))


class ConfigSyncer(DataFileSyncer[UserSettings]):
    JSON_DUMPER_KWARGS = dict(
        strip_privates=True,
        strip_properties=True
    )

    def _dump(self, stream: TextIO):
        writer = CommentsWriter()
        super()._dump(writer.input_stream)
        writer.dump(stream, get_comments_holder(self._class))
