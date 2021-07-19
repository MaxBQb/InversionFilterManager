from time import time
from watchdog.observers.api import DEFAULT_OBSERVER_TIMEOUT
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
from contextlib import contextmanager


class FileTracker:
    def __init__(self, filename: str, sleepy_delay: float = 5):
        self.filename = filename
        self.observer = LazyObserver(sleepy_delay=sleepy_delay)
        self.load_file()
        self.watch_file()
        self.on_file_loaded()

    def watch_file(self):
        handler = PatternMatchingEventHandler(patterns=[".\\" + self.filename],
                                              case_sensitive=True)

        def on_modified(event):
            if not self.observer.is_completely_awake():
                return
            self.reload_file()
            self.on_file_loaded()
            self.on_file_reloaded()

        handler.on_modified = on_modified
        self.observer.schedule(handler, ".")
        self.observer.start()

    def on_file_reloaded(self):
        pass

    def on_file_loaded(self):
        pass

    def load_file(self):
        pass

    def reload_file(self):
        self.load_file()


class LazyObserver(Observer):
    def __init__(self, timeout=DEFAULT_OBSERVER_TIMEOUT,
                 sleepy_delay: float = 5):
        super().__init__(timeout)
        self._is_sleeping = False
        self._still_sleepy = False
        # Ignore any events, in first seconds after awake
        self.sleepy_delay = sleepy_delay
        self._last_awake = 0  # timestamp

    def dispatch_events(self, *args, **kwargs):
        if self._is_sleeping:
            return

        if self._still_sleepy:
            if not self.is_sleepy():
                self._finish_awakening()
            return
        super(LazyObserver, self).dispatch_events(*args, **kwargs)

    @contextmanager
    def overlook(self):
        self.sleep()
        try:
            yield
        finally:
            self.wakeup()

    def sleep(self):
        self._is_sleeping = True
        self._still_sleepy = True

    def wakeup(self):
        if not self._is_sleeping:
            return
        self._is_sleeping = False
        self._last_awake = time()

    def _finish_awakening(self):
        self.event_queue.queue.clear()
        self._still_sleepy = False

    def is_completely_awake(self):
        return not self._is_sleeping and not self._still_sleepy

    def is_sleepy(self):
        return time() - self._last_awake <= self.sleepy_delay
