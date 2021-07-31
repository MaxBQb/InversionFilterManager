import PySimpleGUI as sg
from active_window_checker import WindowInfo
from gui.custom_gui_elements import ButtonSwitchController
from utils import field_names_to_values
import gui.gui_utils as gui_utils


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
