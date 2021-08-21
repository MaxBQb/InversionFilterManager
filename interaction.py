from queue import Queue
import inject
from keyboard import add_hotkey
from active_window_checker import FilterStateController, WindowInfo
from inversion_rules import InversionRulesController
from main_thread_loop import execute_in_main_thread


class InteractionManager:
    state_controller = inject.attr(FilterStateController)
    rules_controller = inject.attr(InversionRulesController)

    def setup(self):
        initial_hotkey = 'ctrl+alt+'

        hotkeys = {
            'plus': self.append_current_app,
            'subtract': self.delete_current_app,
        }

        for k, v in hotkeys.items():
            add_hotkey(initial_hotkey + k, v)

    @execute_in_main_thread()
    def append_current_app(self, winfo: WindowInfo = None):
        from gui import RuleCreationWindow

        winfo = winfo or self.state_controller.last_active_window
        if not winfo:
            return
        rule, name = RuleCreationWindow(winfo).run()
        if name is not None and rule:
            self.rules_controller.add_rule(name, rule)

    @execute_in_main_thread()
    def delete_current_app(self, winfo: WindowInfo = None):
        from gui import RuleRemovingWindow

        winfo = winfo or self.state_controller.last_active_window
        if not winfo:
            return
        if not self.rules_controller.is_inversion_required(winfo):
            return

        rules = RuleRemovingWindow(list(
            self.rules_controller.get_active_rules(winfo, self.rules_controller.rules)
        )).run()
        if rules:
            self.rules_controller.remove_rules(rules)

    @execute_in_main_thread()
    def choose_window_to_remove_rules(self):
        from gui import ChooseRemoveCandidateWindow

        if not self.state_controller.last_active_window:
            return
        winfo = ChooseRemoveCandidateWindow(list(
            self.state_controller.last_active_windows
        )).run()
        if winfo:
            self.delete_current_app(winfo)

    @execute_in_main_thread()
    def choose_window_to_make_rule(self):
        from gui import ChooseAppendCandidateWindow

        if not self.state_controller.last_active_window:
            return
        winfo = ChooseAppendCandidateWindow(list(
            self.state_controller.last_active_windows
        )).run()
        if winfo:
            self.append_current_app(winfo)

    @execute_in_main_thread()
    def request_update(self,
                       latest,
                       file_size,
                       developer_mode: bool,
                       response: Queue):
        from gui import UpdateRequestWindow

        response.put_nowait(UpdateRequestWindow(
            latest, file_size, developer_mode
        ).run())
