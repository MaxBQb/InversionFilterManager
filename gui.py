import PySimpleGUI as sg
from natsort import os_sorted
from active_window_checker import WindowInfo
from custom_gui_elements import ButtonSwitchController, PageSwitchController
from utils import field_names_to_values, ellipsis_trunc
import gui_utils


class RuleCreationWindow(gui_utils.BaseInteractiveWindow):
    title = gui_utils.get_title("create rule")

    @field_names_to_values
    class ButtonState:
        PLAIN: str
        REGEX: str
        DISABLED: str

    @field_names_to_values("-{}-")
    class ID:
        BUTTON_TITLE: str
        BUTTON_PATH: str
        INPUT_TITLE: str
        INPUT_PATH: str
        INPUT_NAME: str
        SUBMIT: str

    id = ID()
    button_states = ButtonState()

    path_button_options = {
        ButtonState.PLAIN: dict(
            tooltip="Simply checks strings equality",
            button_color="#FF4500",
        ),
        ButtonState.REGEX: dict(
            tooltip="Use regex text matching (PRO)",
            button_color="#8B0000",
        ),
    }

    title_button_options = {
        ButtonState.DISABLED: dict(
           tooltip="Skip matching of this field",
           button_color="#2F4F4F",
        ),
    } | path_button_options

    def __init__(self, winfo: WindowInfo):
        super().__init__()
        self.winfo = winfo
        self.path_buttons: ButtonSwitchController = None
        self.title_buttons: ButtonSwitchController = None

    def build_layout(self):
        name = self.winfo.name.removesuffix(".exe").title()
        self.path_buttons = ButtonSwitchController(
            self.path_button_options,
            self.id.BUTTON_PATH,
            gui_utils.BUTTON_DEFAULTS | dict(
                auto_size_button=False
            )
        )
        self.title_buttons = ButtonSwitchController(
            self.title_button_options,
            self.id.BUTTON_TITLE,
            gui_utils.BUTTON_DEFAULTS | dict(
                auto_size_button=False
            )
        )
        label_options = dict(
            auto_size_text=False,
            size=(5, 1)
        )
        self.layout = [
            [gui_utils.center(sg.Text(
                "Here you can choose app, "
                "windows of which will cause inversion"
            ))],
            [
                sg.Text(
                    "Name",
                    tooltip="Name for inversion rule",
                    **label_options
                ),
                sg.InputText(
                    default_text=name,
                    key=self.id.INPUT_NAME,
                    **gui_utils.INPUT_DEFAULTS
                ),
            ],
            [
                sg.Text(
                    "Path",
                    tooltip="Path to program",
                    **label_options
                ),
                sg.InputText(
                    default_text=self.winfo.path,
                    key=self.id.INPUT_PATH,
                    **gui_utils.INPUT_DEFAULTS
                ),
                self.path_buttons.button
            ],
            [
                sg.Text(
                    "Title",
                    tooltip="Text in upper left corner of each program",
                    **label_options
                ),
                sg.InputText(
                    default_text=self.winfo.title,
                    key=self.id.INPUT_TITLE,
                    disabled=True,
                    **gui_utils.INPUT_DEFAULTS
                ),
                self.title_buttons.button
            ],
            [gui_utils.center(sg.Button(
                "OK",
                key=self.id.SUBMIT,
                auto_size_button=False,
                **gui_utils.BUTTON_DEFAULTS
            ))]
        ]

    def set_handlers(self):
        super().set_handlers()
        self.add_event_handlers(
            self.title_buttons.key,
            self.title_buttons.event_handler,
            self.disable_title
        )
        self.add_event_handlers(
            self.path_buttons.key,
            self.path_buttons.event_handler
        )
        self.add_event_handlers(
            self.id.SUBMIT,
            self.on_submit
        )

    def disable_title(self, event: str, window: sg.Window, values):
        window[self.id.INPUT_TITLE].update(
            disabled=self.title_buttons.selected ==
                     self.button_states.DISABLED
        )

    def on_submit(self, event: str, window: sg.Window, values):
        self.context[self.get_key_by_state(self.path_buttons, 'path')] = values[self.id.INPUT_PATH]
        title_key = self.get_key_by_state(self.title_buttons, 'title')
        if title_key:
            self.context[title_key] = values[self.id.INPUT_TITLE]
        self.context['name'] = values[self.id.INPUT_NAME]
        self.close()

    def get_key_by_state(self, button_switch: ButtonSwitchController, key: str):
        if button_switch.selected == self.button_states.DISABLED:
            return
        if button_switch.selected == self.button_states.REGEX:
            key += '_regex'
        return key


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