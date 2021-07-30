from PySimpleGUI import Button, Window
from utils import rename_key, cycled_shift
from functools import cached_property


class ButtonSwitchController:
    def __init__(self,
                 options: dict[str, dict],
                 key: str,
                 common_options: dict = {}):
        self.states = tuple(options)
        self.options = dict(options)
        self.common_options = common_options
        for state in self.states:
            # default param set + deepcopy
            self.options[state] = {
                'button_text': state
            } | self.options[state]
        self.key = key
        self._tooltips = {}
        self.selected = self.states[0]

    @cached_property
    def button(self):
        button = Button(**(
            self.options[self.selected] |
            self.common_options
        ), key=self.key)
        for state in self.states:
            rename_key(self.options[state], 'button_text', 'text')
            if 'tooltip' in self.options[state]:
                self._tooltips[state] = self.options[state].pop('tooltip')
        return button

    def get_next_state(self):
        return self.states[cycled_shift(
            self.states.index(self.selected),
            len(self.states)
        )]

    def handle_event(self, event, window: Window):
        if event != self.key:
            return False
        self.change_state(self.get_next_state(), window)
        return True

    def change_state(self, new_state: str, window: Window):
        btn: Button = window[self.key]
        options = self.options[new_state]
        self.selected = new_state
        tooltip = self._tooltips.get(new_state)
        if tooltip is not None:
            btn.set_tooltip(tooltip)
        btn.update(**options)
