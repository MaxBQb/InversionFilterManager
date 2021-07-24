from PySimpleGUI import Button, Window
from gui.gui_utils import BUTTON_DEFAULTS


class ButtonSwitchController:
    def __init__(self, options: dict[str, dict], key: str):
        self.options = dict(options)
        self.states = tuple(options.keys())
        self.key = key
        self.keys = [
            self.get_specific_key(state)
            for state in self.states
        ]
        self.selected = self.keys[0]

    def get_buttons(self, common_options=BUTTON_DEFAULTS):
        return [
            Button(**(self.get_button_options(state) | common_options))
            for state in self.states
        ]

    def get_button_options(self, state: str) -> dict:
        return self.options.get(state) | dict(
            button_text=state,
            metadata=state,
            key=self.get_specific_key(state),
            visible=state == self.states[0]
        )

    def get_specific_key(self, state: str) -> str:
        return self.key + state + "-"

    def is_selected(self, state: str):
        return self.selected == self.get_specific_key(state)

    def select_next(self):
        self.selected = self.get_next_cycled(
            self.keys, self.selected
        )
        return self.selected

    @staticmethod
    def get_next_cycled(array: list, current):
        return array[(array.index(current) + 1) % len(array)]

    def handle_event(self, event, window: Window):
        if event not in self.keys:
            return False
        window[event].update(visible=False)
        window[self.select_next()].update(visible=True)
        return True
