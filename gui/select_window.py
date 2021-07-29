import PySimpleGUI as sg
from active_window_checker import WindowInfo
from gui.switching_button import ButtonSwitchController
from utils import field_names_to_values
import gui.gui_utils as gui_utils


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


WINDOW_TITLE = gui_utils.get_title("select window")

PATH_BUTTON_OPTIONS = {
    ButtonState.PLAIN: dict(
        tooltip="Simply checks strings equality",
        button_color="#FF4500",
    ),
    ButtonState.REGEX: dict(
        tooltip="Use regex text matching (PRO)",
        button_color="#8B0000",
    ),
}

TITLE_BUTTON_OPTIONS = {
                           ButtonState.DISABLED: dict(
                               tooltip="Skip matching of this field",
                               button_color="#2F4F4F",
                           ),
                       } | PATH_BUTTON_OPTIONS


def select_window(winfo: WindowInfo):
    path_buttons = ButtonSwitchController(
        PATH_BUTTON_OPTIONS,
        ID.BUTTON_PATH,
        gui_utils.BUTTON_DEFAULTS | dict(
            auto_size_button=False
        )
    )
    title_buttons = ButtonSwitchController(
        TITLE_BUTTON_OPTIONS,
        ID.BUTTON_TITLE,
        gui_utils.BUTTON_DEFAULTS | dict(
            auto_size_button=False
        )
    )

    window = sg.Window(WINDOW_TITLE, build_view(
        winfo.title,
        winfo.path,
        winfo.name,
        path_buttons,
        title_buttons
    ),
                       finalize=True,
                       element_padding=(12, 12),
                       disable_minimize=True
                       )
    window.bring_to_front()
    gui_utils.deny_maximize(window)
    gui_utils.deny_minimize(window)
    context = {}

    # Create an event loop
    while True:
        event, values = window.read()

        if title_buttons.handle_event(event, window):
            window[ID.INPUT_TITLE].update(
                disabled=title_buttons.selected == ButtonState.DISABLED
            )

        path_buttons.handle_event(event, window)
        if event == ID.SUBMIT:
            context[get_key_by_state(path_buttons, 'path')] = values[ID.INPUT_PATH]
            title_key = get_key_by_state(title_buttons, 'title')
            if title_key:
                context[title_key] = values[ID.INPUT_TITLE]
            name = values[ID.INPUT_NAME]
            break

        if event == sg.WIN_CLOSED:
            break

    window.close()
    if not context or not name:
        return None
    return context, name


def get_key_by_state(button_switch: ButtonSwitchController, key: str):
    if button_switch.selected == ButtonState.DISABLED:
        return
    if button_switch.selected == ButtonState.REGEX:
        key += '_regex'
    return key


def build_view(title: str, path: str, name: str,
               path_buttons, title_buttons):
    name = name.removesuffix(".exe").title()
    label_options = dict(
        auto_size_text=False,
        size=(5, 1)
    )
    return gui_utils.create_layout(
        WINDOW_TITLE,
        [
            gui_utils.center(sg.Text(
                "Here you can choose app, "
                "windows of which will cause inversion"
            ))
        ],
        [
            sg.Text(
                "Name",
                tooltip="Name for inversion rule",
                **label_options
            ),
            sg.InputText(
                default_text=name,
                key=ID.INPUT_NAME,
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
                default_text=path,
                key=ID.INPUT_PATH,
                **gui_utils.INPUT_DEFAULTS
            ),
            path_buttons.button
        ],
        [
            sg.Text(
                "Title",
                tooltip="Text in upper left corner of each program",
                **label_options
            ),
            sg.InputText(
                default_text=title,
                key=ID.INPUT_TITLE,
                disabled=True,
                **gui_utils.INPUT_DEFAULTS
            ),
            title_buttons.button
        ],
        [
            gui_utils.center(sg.Button(
                "OK",
                key=ID.SUBMIT,
                auto_size_button=False,
                **gui_utils.BUTTON_DEFAULTS
            )),
        ]
    )
