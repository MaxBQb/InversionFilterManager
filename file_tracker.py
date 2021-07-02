import time
from watchdog.observers.api import DEFAULT_OBSERVER_TIMEOUT
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
from contextlib import contextmanager


class FileTracker:
    def __init__(self, filename: str):
        self.filename = filename
        self.observer = LazyObserver()
        self.load_file()
        self.watch_file()
        self.on_file_loaded()

    def watch_file(self):
        handler = PatternMatchingEventHandler(patterns=[".\\" + self.filename],
                                              case_sensitive=True)

        def on_modified(event):
            self.reload_file()
            self.on_file_loaded()
            self.on_file_reloaded()

        handler.on_modified = on_modified
        self.observer.schedule(handler, ".")
        self.observer.start()

    @staticmethod
    def on_file_reloaded():
        pass

    @staticmethod
    def on_file_loaded():
        pass

    def load_file(self):
        pass

    def reload_file(self):
        self.load_file()


class LazyObserver(Observer):
    def __init__(self, timeout=DEFAULT_OBSERVER_TIMEOUT):
        super().__init__(timeout)
        self._sleeping = False

    def dispatch_events(self, *args, **kwargs):
        if not self._sleeping:
            super(LazyObserver, self).dispatch_events(*args, **kwargs)

    @contextmanager
    def overlook(self):
        self.sleep()
        yield
        self.wakeup()

    def sleep(self):
        self._sleeping = True

    def wakeup(self):
        time.sleep(self.timeout)  # allow interim events to be queued
        self.event_queue.queue.clear()
        self._sleeping = False
