import os
import inject
import jsons
import yaml
from commented_config import CommentsWriter, get_comments_holder
from file_tracker import FileTracker
from inversion_rules import InversionRulesController, InversionRule, RULES
from auto_update import AutoUpdater
from typing import TypeVar, Generic


T = TypeVar('T')


class DataFileSyncer(FileTracker, Generic[T]):
    def __init__(self, filename: str, data: T, data_type=None):
        self._data: T = None
        self.data = data
        self._class = data_type or type(data)
        super().__init__(filename + ".yaml")

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, new_data: T):
        self._data = new_data
        self._data._syncer = self

    def load_file(self):
        if not os.path.exists(self.filename):
            self.save_file()
            return

        with self.observer.overlook():
            with open(self.filename, encoding="utf-8-sig") as f:
                new_data: T = self._load(f)

        if new_data != self._data:
            self.data = new_data

        self.save_file()

    def _load(self, stream):
        return jsons.load(yaml.load(
            stream, yaml.CSafeLoader
        ) or {}, self._class)

    def save_file(self):
        with self.observer.overlook():
            with open(self.filename, "w", encoding="utf-8") as f:
                self._dump(f)

    def _dump(self, stream, json_kwargs={}, yaml_kwargs={}):
        yaml.dump(jsons.dump(self._data, **json_kwargs),
                  stream, yaml.CDumper, **yaml_kwargs)

    def on_file_reloaded(self):
        print(f"Changes for '{self.filename}' applied")


class ConfigSyncer(DataFileSyncer):
    updater = inject.attr(AutoUpdater)

    def setup(self):
        self.updater.move_on_update(self.filename)

    def _dump(self, stream, json_kwargs={}, yaml_kwargs={}):
        writer = CommentsWriter()
        super()._dump(
            writer.input_stream,
            json_kwargs | dict(
                strip_privates=True,
            ), yaml_kwargs)
        writer.dump(stream, get_comments_holder(self._class))


class RulesSyncer(DataFileSyncer):
    updater = inject.attr(AutoUpdater)

    def __init__(self, name: str, rules_controller: InversionRulesController):
        self.rules_controller = rules_controller
        self.rules_controller._syncer = self
        self.rules_controller.on_modified = self.save_file
        super().__init__(name, {}, RULES)

    def setup(self):
        self.updater.move_on_update(self.filename)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, new_data: T):
        self._data = new_data

    def on_file_loaded(self):
        self.rules_controller.load_rules(self.data)

    def _dump(self, stream, json_kwargs={}, yaml_kwargs={}):
        if not self._data:
            stream.truncate(0)
            return
        super()._dump(
            stream, json_kwargs | dict(
                strip_properties=True,
                strip_privates=True,
                strip_nulls=True
            ), yaml_kwargs
        )
