from PySimpleGUI import Button, Window, Column
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

    def select_next(self):
        self.selected = self.states[cycled_shift(
            self.states.index(self.selected),
            len(self.states)
        )]

    def handle_event(self, event, window: Window):
        if event != self.key:
            return False
        btn: Button = window[event]
        self.select_next()
        options = self.options[self.selected]
        tooltip = self._tooltips.get(self.selected)
        if tooltip is not None:
            btn.set_tooltip(tooltip)
        btn.update(**options)
        return True
