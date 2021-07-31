import PySimpleGUI as sg
from gui.custom_gui_elements import ButtonSwitchController, PageSwitchController
from utils import field_names_to_values, ellipsis_trunc
import gui.gui_utils as gui_utils
from natsort import os_sorted


class RuleRemovingWindow(gui_utils.BaseInteractiveWindow):
    title = gui_utils.get_title("select rules")

    @field_names_to_values
    class ButtonState:
        SKIP: str
        REMOVE: str

    @field_names_to_values("-{}-")
    class ID:
        ACTION: str
        COMMON_ACTION: str
        PAGES: str
        SUBMIT: str

    id = ID()
    button_states = ButtonState()

    BUTTON_OPTIONS = {
        ButtonState.SKIP: dict(
            tooltip="Preserve this rule",
            button_color="#2F4F4F",
        ),
        ButtonState.REMOVE: dict(
            tooltip="Remove this rule",
            button_color="#8B0000",
        ),
    }

    def __init__(self, rules: list[str]):
        super().__init__()
        self.rules = os_sorted(rules)
        self.actions: list[ButtonSwitchController] = []
        self.common_action: ButtonSwitchController = None
        self.pages: PageSwitchController = None
        self.context = {
            'remove': set()
        }
        self.rules_to_remove = self.context['remove']

    def build_layout(self):
        pad = 6, 6

        common_switcher_options = gui_utils.BUTTON_DEFAULTS | dict(
            pad=pad,
            use_ttk_buttons=False,
            auto_size_button=False
        )

        self.common_action = ButtonSwitchController(
            self.BUTTON_OPTIONS,
            self.id.COMMON_ACTION,
            common_switcher_options
        )

        self.pages = PageSwitchController.from_list(
            self.build_rule_selection_buttons(
                common_switcher_options
            )
        )(key=self.id.PAGES)

        common_switcher_options = gui_utils.BUTTON_DEFAULTS | dict(
            pad=pad,
            auto_size_button=False
        )
        single_rule = len(self.rules) == 1
        self.layout = [
            [sg.Text(("Rule" if single_rule else "List of rules") +
                     " associated with this window:")],
            [sg.Text("Common state:", pad=(0, 0)), self.common_action.button] if not single_rule else [],
            [self.pages.get_pages_holder()],
            [*self.pages.get_controls(gui_utils.BUTTON_DEFAULTS | dict(
                disabled_button_color="#21242c",
                pad=(4, 4)
            ))],
            [sg.Button("OK", key=self.id.SUBMIT,
                       **common_switcher_options)]
        ]

    def build_rule_selection_buttons(self, common_switcher_options) -> list[sg.Button]:
        rule_buttons = []
        h_pad, v_pad = common_switcher_options['pad']
        for i, name in enumerate(self.rules):
            rule_buttons.append(
                sg.Button(
                    ellipsis_trunc(name, width=10),
                    font=("Consolas", 10),
                    **(common_switcher_options |
                       dict(pad=((h_pad * 2, h_pad), v_pad)))
                )
            )
            self.actions.append(
                ButtonSwitchController(
                    self.BUTTON_OPTIONS,
                    gui_utils.join_id(self.id.ACTION, str(i)),
                    common_switcher_options | dict(
                        metadata=name
                    )
                )
            )
            rule_buttons.append(self.actions[-1].button)
        return rule_buttons

    def set_handlers(self):
        for action in self.actions:
            self.add_event_handlers(
                action.key,
                self.get_on_action_click_handler(action)
            )
        self.add_event_handlers(
            self.common_action.key,
            self.common_action.event_handler,
            self.on_common_action_click
        )
        self.add_event_handlers(
            self.id.SUBMIT,
            self.make_handler(self.close)
        )
        self.add_event_handlers(
            sg.WIN_CLOSED,
            self.on_closed
        )

    def init_window(self, **kwargs):
        super().init_window(
            element_justification='center'
        )

    def get_on_action_click_handler(self, action: ButtonSwitchController):
        def on_action_click(event: str,
                            window: sg.Window,
                            values):
            action.event_handler(event, window, values)
            name = window[event].metadata
            if action.selected == self.button_states.REMOVE:
                self.rules_to_remove.add(name)
            else:
                self.rules_to_remove.remove(name)
        return on_action_click

    def on_common_action_click(self,
                               event: str,
                               window: sg.Window,
                               values):
        for action in self.actions:
            action.change_state(self.common_action.selected, window)

        if self.common_action.selected == self.button_states.REMOVE:
            self.rules_to_remove.update(self.rules)
        else:
            self.rules_to_remove.clear()

    def on_unhandled_event(self,
                           event: str,
                           window: sg.Window,
                           values):
        self.pages.handle_event(event, window)

    def on_closed(self,
                  event: str,
                  window: sg.Window,
                  values):
        self.context = None
        self.close()
