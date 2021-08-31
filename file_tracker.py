import os
from contextlib import contextmanager
from time import time
from typing import Generic, TypeVar
import inject
import jsons
import yaml
from abc import ABC
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer as DirectoryObserver
from watchdog.observers.api import DEFAULT_OBSERVER_TIMEOUT
from _meta import IndirectDependency


T = TypeVar('T')


class DataFileSyncer(Generic[T]):
    JSON_DUMPER_KWARGS = {}
    YAML_DUMPER_KWARGS = {}

    def __init__(self,
                 filename: str,
                 data: T,
                 data_type=None,
                 extension="yaml"):
        self.data = data
        self._class = data_type or type(data)
        self.filename = f'{filename}.{extension}'
        self.dir_observer = LazyDirectoryObserver()

    def start(self):
        self.load_file()
        self._watch_file()

    @inject.params(carryon=IndirectDependency.CARRYON_BEFORE_UPDATE)
    def preserve_on_update(self, carryon: list[str]):
        carryon.append(self.filename)

    def _watch_file(self):
        handler = PatternMatchingEventHandler(patterns=[".\\" + self.filename],
                                              case_sensitive=True)

        def on_modified(event):
            if not self.dir_observer.is_completely_awake():
                return
            self.load_file()

        handler.on_modified = on_modified
        self.dir_observer.schedule(handler, ".")
        self.dir_observer.start()

    def load_file(self):
        if not os.path.exists(self.filename):
            self.save_file()
            return

        with self.dir_observer.overlook():
            with open(self.filename, encoding="utf-8-sig") as f:
                new_data: T = self._load(f)

        if new_data != self.data:
            self.data = new_data
            self.on_file_reloaded()

        self.save_file()

    def _load(self, stream):
        return jsons.load(yaml.load(
            stream, yaml.CSafeLoader
        ) or {}, self._class)

    def save_file(self):
        with self.dir_observer.overlook():
            with open(self.filename, "w", encoding="utf-8") as f:
                self._dump(f)

    def _dump(self, stream):
        yaml.dump(jsons.dump(self.data, **self.JSON_DUMPER_KWARGS),
                  stream, yaml.CDumper, **self.YAML_DUMPER_KWARGS)

    def on_file_reloaded(self):
        pass


class Syncable(ABC):
    def __init__(self, syncer: DataFileSyncer):
        self._syncer = syncer
        self.filename = syncer.filename

    def load(self):
        self._syncer.load_file()

    def save(self):
        self._syncer.save_file()


class LazyDirectoryObserver(DirectoryObserver):
    def __init__(self, timeout=DEFAULT_OBSERVER_TIMEOUT):
        super().__init__(timeout)
        self._is_sleeping = False
        self._still_sleepy = False
        self._awake_complete_time = 0  # timestamp

    def dispatch_events(self, *args, **kwargs):
        if self._is_sleeping:
            return

        if self._still_sleepy:
            if not self.is_sleepy():
                self._finish_awakening()
            return
        
        super(LazyDirectoryObserver, self).dispatch_events(*args, **kwargs)

    @contextmanager
    def overlook(self):
        self.sleep()
        try:
            yield
        finally:
            self.wakeup()

    def sleep(self):
        if not self.is_alive():
            return
        self._is_sleeping = True
        self._still_sleepy = True

    def wakeup(self):
        if not self._is_sleeping:
            return
        self._is_sleeping = False
        self._awake_complete_time = time() + self.timeout

    def _finish_awakening(self):
        self.event_queue.queue.clear()
        self._still_sleepy = False

    def is_completely_awake(self):
        return not self._is_sleeping and not self._still_sleepy

    def is_sleepy(self):
        return time() <= self._awake_complete_time
