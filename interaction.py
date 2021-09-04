from contextlib import contextmanager
from queue import Queue
import inject
import keyboard
import gui
import gui_utils
from active_window_checker import FilterStateController, WindowInfo
from app_close import AppCloseManager
from inversion_rules import InversionRulesController
from main_thread_loop import execute_in_main_thread


class InteractionManager:
    state_controller = inject.attr(FilterStateController)
    rules_controller = inject.attr(InversionRulesController)
    close_manager = inject.attr(AppCloseManager)

    def __init__(self):
        self._current_window: gui_utils.BaseNonBlockingWindow = None

    @contextmanager
    def _open_window(self, window: gui_utils.BaseNonBlockingWindow):
        try:
            self._current_window = window
            yield window
        finally:
            self._current_window = None

    def close_current_window(self):
        if self._current_window is not None:
            self._current_window.send_close_event()

    def setup(self):
        self.close_manager.add_exit_handler(self.close_current_window)
        gui_utils.init_theme()
        initial_hotkey = 'ctrl+alt+'

        hotkeys = {
            'plus': self.append_current_app,
            'subtract': self.delete_current_app,
        }

        for k, v in hotkeys.items():
            keyboard.add_hotkey(initial_hotkey + k, v)

    @execute_in_main_thread()
    def append_current_app(self, winfo: WindowInfo = None):
        winfo = winfo or self.state_controller.last_active_window
        if not winfo:
            return

        with self._open_window(gui.RuleCreationWindow(winfo)) as window:
            rule, name = window.run()
            if name is not None and rule:
                self.rules_controller.add_rule(name, rule)

    @execute_in_main_thread()
    def delete_current_app(self, winfo: WindowInfo = None):
        winfo = winfo or self.state_controller.last_active_window
        if not winfo:
            return

        if not self.rules_controller.has_active_rules(winfo):
            return

        active_rules = list(
            self.rules_controller.get_active_rules(
                winfo, self.rules_controller.rules
            )
        )

        with self._open_window(gui.RuleRemovingWindow(active_rules)) as window:
            rules = window.run()

            if rules:
                self.rules_controller.remove_rules(rules)

    @execute_in_main_thread()
    def choose_window_to_remove_rules(self):
        if not self.state_controller.last_active_window:
            return

        candidates = [
            winfo for winfo in self.state_controller.last_active_windows
            if self.rules_controller.has_active_rules(winfo)
        ]

        if not candidates:
            return

        if len(candidates) == 1:
            self.delete_current_app(candidates[0])
            return

        with self._open_window(gui.ChooseRemoveCandidateWindow(candidates)) as window:
            winfo = window.run()

            if winfo:
                self.delete_current_app(winfo)

    @execute_in_main_thread()
    def choose_window_to_make_rule(self):
        if not self.state_controller.last_active_window:
            return

        candidates = list(self.state_controller.last_active_windows)

        if len(candidates) == 1:
            self.append_current_app(candidates[0])
            return

        with self._open_window(gui.ChooseAppendCandidateWindow(candidates)) as window:
            winfo = window.run()

            if winfo:
                self.append_current_app(winfo)

    @execute_in_main_thread()
    def request_update(self,
                       latest,
                       file_size,
                       response: Queue):
        with self._open_window(gui.UpdateRequestWindow(latest, file_size)) as window:
            response.put_nowait(window.run())
