import PySimpleGUI as sg
from natsort import os_sorted
from active_window_checker import WindowInfo
from custom_gui_elements import ButtonSwitchController, PageSwitchController
from utils import StrHolder, ellipsis_trunc
import gui_utils
from gui_utils import BaseInteractiveWindow, BaseNonBlockingWindow
import inject
from apps_rules import AppsRulesController, AppRule


class RuleCreationWindow(BaseInteractiveWindow):
    title = gui_utils.get_title("create rule")

    class ButtonState(StrHolder):
        PLAIN: str
        REGEX: str
        DISABLED: str

    class ID(BaseInteractiveWindow.ID):
        BUTTON_TITLE: str
        BUTTON_PATH: str
        INPUT_TITLE: str
        INPUT_PATH: str
        INPUT_NAME: str

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

    common_options = gui_utils.BUTTON_DEFAULTS | dict(
        auto_size_button=False
    )

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
            self.ID.BUTTON_PATH,
            self.common_options
        )
        self.title_buttons = ButtonSwitchController(
            self.title_button_options,
            self.ID.BUTTON_TITLE,
            self.common_options
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
                    key=self.ID.INPUT_NAME,
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
                    key=self.ID.INPUT_PATH,
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
                    key=self.ID.INPUT_TITLE,
                    disabled=True,
                    **gui_utils.INPUT_DEFAULTS
                ),
                self.title_buttons.button
            ],
        ]

    def dynamic_build(self):
        super().dynamic_build()
        inputs = (
            self.ID.INPUT_TITLE,
            self.ID.INPUT_PATH,
            self.ID.INPUT_NAME
        )
        for input in inputs:
            self.window[input].Widget.config(
                **gui_utils.INPUT_EXTRA_DEFAULTS
            )

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
        window[self.ID.INPUT_TITLE].update(
            disabled=self.title_buttons.selected ==
                     self.ButtonState.DISABLED
        )

    def on_submit(self, event: str, window: sg.Window, values):
        self.set_key_from_state(self.path_buttons.selected, 'path', values[self.ID.INPUT_PATH])
        self.set_key_from_state(self.title_buttons.selected, 'title', values[self.ID.INPUT_TITLE])
        self.name = values[self.ID.INPUT_NAME]
        self.close()

    def set_key_from_state(self, button_state: ButtonState, key: str, value):
        if button_state == self.ButtonState.DISABLED:
            return

        if button_state == self.ButtonState.REGEX:
            key += '_regex'

        self.raw_rule[key] = value


class RuleRemovingWindow(BaseInteractiveWindow):
    all_rules = inject.attr(AppsRulesController)
    title = gui_utils.get_title("select rules")

    class ButtonState(StrHolder):
        SKIP: str
        REMOVE: str

    class ID(BaseInteractiveWindow.ID):
        ACTION: str
        DESCRIPTION: str
        COMMON_ACTION: str
        PAGES: str

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
            auto_size_button=False,
        )

        self.common_action = ButtonSwitchController(
            self.BUTTON_OPTIONS,
            self.ID.COMMON_ACTION,
            common_switcher_options
        )

        self.pages = PageSwitchController.from_list(
            self.build_rule_selection_buttons(
                common_switcher_options
            )
        )(key=self.ID.PAGES)

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
            self.description_button_keys.append(gui_utils.join_id(self.ID.DESCRIPTION, str(i)))
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
                    gui_utils.join_id(self.ID.ACTION, str(i)),
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
        self._open_dependent_window(
            RuleDescriptionWindow(self.all_rules.rules[name], name)
        )

    def on_submit(self,
                  event: str,
                  window: sg.Window,
                  values):
        self.rules_to_remove = {
            window[action.key].metadata
            for action in self.actions
            if action.selected == self.ButtonState.REMOVE
        }
        self.close()


class RuleDescriptionWindow(BaseNonBlockingWindow):
    title = gui_utils.get_title("rule info")

    class ID(BaseNonBlockingWindow.ID):
        INPUT: str

    def __init__(self, rule: AppRule, name: str):
        super().__init__()
        self.rule = rule
        self.name = name
        self.inputs: list[str] = None

    def build_layout(self):
        description = dict(
            name=self.name,
        ) | {
            k: v for k, v in vars(self.rule).items()
            if not k.startswith('_') and v
        }
        size = (len(max(description.keys(), key=len)), 1)
        font = gui_utils.INPUT_DEFAULTS['font']
        self.inputs = [
            gui_utils.join_id(self.ID.INPUT, name)
            for name in description
        ]
        self.layout = [
            [sg.Text(
                label.title() + ':',
                auto_size_text=False,
                font=font,
                size=size,
             ),
             sg.InputText(
                 content,
                 readonly=True,
                 key=input_key,
                 **gui_utils.INPUT_DEFAULTS
             )]
            for (label, content), input_key in zip(description.items(), self.inputs)
        ]

    def dynamic_build(self):
        super().dynamic_build()
        for input in self.inputs:
            self.window[input].Widget.config(
                **gui_utils.INPUT_EXTRA_DEFAULTS
            )
        self.inputs = None


class UpdateRequestWindow(gui_utils.ConfirmationWindow):
    title = gui_utils.get_title("new release is out!")

    class ID(gui_utils.ConfirmationWindow.ID):
        INPUT: str

    def __init__(self, latest_version: str, file_size: int):
        super().__init__("Do you want to install new release?")
        self.latest_version = latest_version
        self.file_size = file_size

    def build_layout(self):
        import _meta as app
        from hurry.filesize import size, alternative

        self.layout = [
            [gui_utils.center(sg.Text('Update info', font=("Verdana", 18)))]
        ]

        description = dict(
            app_name=app.__product_name__,
            current_version=app.__version__,
            latest_version=self.latest_version,
            release_size=size(self.file_size, alternative),
        )
        label_size = (len(max(description.keys(), key=len))+1, 1)
        input_size = (len(max(description.values(), key=len))+4, 1)
        font = gui_utils.INPUT_DEFAULTS['font']
        self.inputs = [
            gui_utils.join_id(self.ID.INPUT, name)
            for name in description
        ]
        self.layout += [
            [sg.Text(
                label.capitalize().replace('_', ' ') + ':',
                auto_size_text=False,
                font=font,
                size=label_size,
             ),
             sg.InputText(
                 content,
                 readonly=True,
                 key=input_key,
                 size=input_size,
                 **gui_utils.INPUT_DEFAULTS
             )]
            for (label, content), input_key in zip(description.items(), self.inputs)
        ]
        super().build_layout()

    def dynamic_build(self):
        super().dynamic_build()
        for input in self.inputs:
            self.window[input].Widget.config(
                **gui_utils.INPUT_EXTRA_DEFAULTS
            )
        self.inputs = None
