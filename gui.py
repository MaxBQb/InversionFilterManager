import PySimpleGUI as sg
from natsort import os_sorted
from active_window_checker import WindowInfo
from custom_gui_elements import ButtonSwitchController, PageSwitchController
from utils import field_names_to_values, ellipsis_trunc
import gui_utils
from gui_utils import BaseInteractiveWindow, BaseNonBlockingWindow
import inject
from apps_rules import AppsRulesController, AppRule
from typing import Callable


class RuleCreationWindow(BaseInteractiveWindow):
    title = gui_utils.get_title("create rule")

    @field_names_to_values
    class ButtonState:
        PLAIN: str
        REGEX: str
        DISABLED: str

    @field_names_to_values("-{}-")
    class ID(BaseInteractiveWindow.ID):
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
        self.name: str = None
        self.raw_rule = {}

    def run(self) -> tuple[dict, str]:
        super().run()
        return self.raw_rule, self.name

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
                    **label_options
                ),
                sg.InputText(
                    tooltip="Name for inversion rule",
                    default_text=name,
                    key=self.id.INPUT_NAME,
                    **gui_utils.INPUT_DEFAULTS
                ),
            ],
            [
                sg.Text(
                    "Path",
                    **label_options
                ),
                sg.InputText(
                    tooltip="Path to program",
                    default_text=self.winfo.path,
                    key=self.id.INPUT_PATH,
                    **gui_utils.INPUT_DEFAULTS
                ),
                self.path_buttons.button
            ],
            [
                sg.Text(
                    "Title",
                    **label_options
                ),
                sg.InputText(
                    tooltip="Text in upper left corner of each program",
                    default_text=self.winfo.title,
                    key=self.id.INPUT_TITLE,
                    disabled=True,
                    **gui_utils.INPUT_DEFAULTS
                ),
                self.title_buttons.button
            ],
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

    def disable_title(self, event: str, window: sg.Window, values):
        window[self.id.INPUT_TITLE].update(
            disabled=self.title_buttons.selected ==
                     self.button_states.DISABLED
        )

    def on_submit(self, event: str, window: sg.Window, values):
        self.set_key_from_state(self.path_buttons.selected, 'path', values[self.id.INPUT_PATH])
        self.set_key_from_state(self.title_buttons.selected, 'title', values[self.id.INPUT_TITLE])
        self.name = values[self.id.INPUT_NAME]
        self.close()

    def set_key_from_state(self, button_state: ButtonState, key: str, value):
        if button_state == self.button_states.DISABLED:
            return

        if button_state == self.button_states.REGEX:
            key += '_regex'

        self.raw_rule[key] = value


class RuleRemovingWindow(BaseInteractiveWindow):
    all_rules = inject.attr(AppsRulesController)
    title = gui_utils.get_title("select rules")

    @field_names_to_values
    class ButtonState:
        SKIP: str
        REMOVE: str

    @field_names_to_values("-{}-")
    class ID(BaseInteractiveWindow.ID):
        ACTION: str
        DESCRIPTION: str
        COMMON_ACTION: str
        PAGES: str

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
        self.description_button_keys: list[str] = []
        self.before_close: list[Callable] = []
        self.actions: list[ButtonSwitchController] = []
        self.common_action: ButtonSwitchController = None
        self.pages: PageSwitchController = None
        self.rules_to_remove: set[str] = set()

    def run(self) -> set[str]:
        super().run()
        return self.rules_to_remove

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

        single_rule = len(self.rules) == 1
        self.layout = [
            [sg.Text(("Rule" if single_rule else "List of rules") +
                     " associated with this window:")],
            [sg.Text("Common state:", pad=(0, 0)), self.common_action.button] if not single_rule else [],
            [self.pages.get_pages_holder()],
            [*self.pages.get_controls(gui_utils.BUTTON_DEFAULTS | dict(
                pad=pad
            ))]
        ]

    def build_rule_selection_buttons(self, common_switcher_options) -> list[sg.Button]:
        rule_buttons = []
        h_pad, v_pad = common_switcher_options['pad']
        for i, name in enumerate(self.rules):
            self.description_button_keys.append(gui_utils.join_id(self.id.DESCRIPTION, str(i)))
            rule_buttons.append(
                sg.Button(
                    ellipsis_trunc(name, width=10),
                    font=("Consolas", 10),
                    **(common_switcher_options |
                       dict(pad=((h_pad * 2, h_pad), v_pad))),
                    key=self.description_button_keys[-1],
                    metadata=name
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
        super().set_handlers()
        for action in self.actions:
            self.add_event_handlers(
                action.key,
                action.event_handler
            )
        for key in self.description_button_keys:
            self.add_event_handlers(
                key,
                self.on_description_open
            )
        self.description_button_keys = None
        self.add_event_handlers(
            self.common_action.key,
            self.common_action.event_handler,
            self.on_common_action_click
        )

    def init_window(self, **kwargs):
        super().init_window(
            element_justification='center'
        )

    def close(self):
        for action in self.before_close:
            action()
        super().close()

    def on_common_action_click(self,
                               event: str,
                               window: sg.Window,
                               values):
        for action in self.actions:
            action.change_state(
                self.common_action.selected,
                window
            )

    def on_unhandled_event(self,
                           event: str,
                           window: sg.Window,
                           values):
        self.pages.handle_event(event, window)

    def on_description_open(self,
                            event: str,
                            window: sg.Window,
                            values):
        name = window[event].metadata
        description_window = RuleDescriptionWindow(self.all_rules.rules[name], name)
        description_window.run()
        self.before_close.append(description_window.close)

    def on_submit(self,
                  event: str,
                  window: sg.Window,
                  values):
        self.rules_to_remove = {
            window[action.key].metadata
            for action in self.actions
            if action.selected == self.button_states.REMOVE
        }
        self.close()


class RuleDescriptionWindow(BaseNonBlockingWindow):
    title = gui_utils.get_title("rule info")

    def __init__(self, rule: AppRule, name: str):
        super().__init__()
        self.rule = rule
        self.name = name

    def build_layout(self):
        description = dict(
            name=self.name,
        ) | {
            k: v for k, v in vars(self.rule).items()
            if not k.startswith('_') and v
        }
        size = (len(max(description.keys(), key=len)), 1)
        font = ('Consolas', 12)
        self.layout = [
            [sg.Text(
                label.title() + ':',
                auto_size_text=False,
                font=font,
                size=size
            ),
             sg.InputText(
                 content,
                 readonly=True,
                 font=font,
                 **gui_utils.INPUT_DEFAULTS
             )]
            for label, content in description.items()
        ]
