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

PATH_BUTTONS = ButtonSwitchController(PATH_BUTTON_OPTIONS, ID.BUTTON_PATH)
TITLE_BUTTONS = ButtonSwitchController(TITLE_BUTTON_OPTIONS, ID.BUTTON_TITLE)


def select_window(winfo: WindowInfo):
    window = sg.Window(WINDOW_TITLE, build_view(
        winfo.title,
        winfo.path,
        winfo.name,
    ), finalize=True)
    gui_utils.deny_maximize(window)
    gui_utils.deny_minimize(window)
    context = {}

    # Create an event loop
    while True:
        event, values = window.read()

        if TITLE_BUTTONS.handle_event(event, window):
            window[ID.INPUT_TITLE].update(
                disabled=TITLE_BUTTONS.is_selected(ButtonState.DISABLED)
            )

        PATH_BUTTONS.handle_event(event, window)
        if event == ID.SUBMIT:
            context[get_key_by_state(PATH_BUTTONS, 'path')] = values[ID.INPUT_PATH]
            title_key = get_key_by_state(TITLE_BUTTONS, 'title')
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
    if button_switch.is_selected(ButtonState.DISABLED):
        return
    if button_switch.is_selected(ButtonState.REGEX):
        key += '_regex'
    return key


def build_view(title: str, path: str, name: str):
    name = name.removesuffix(".exe").title()
    pad = h_pad, v_pad = 12, 12
    common_switcher_options = gui_utils.BUTTON_DEFAULTS | dict(
        pad=pad,
        auto_size_button=False
    )
    return gui_utils.create_layout(
        WINDOW_TITLE,
        [sg.Text("Here you can choose app, windows of which will cause inversion",
                 pad=((96, 0), v_pad))],
        [
            sg.Text("Name", tooltip="Name for inversion rule"),
            sg.InputText(default_text=name, key=ID.INPUT_NAME,
                         **gui_utils.INPUT_DEFAULTS, pad=pad, ),
        ],
        [
            sg.Text("Path ", tooltip="Path to program"),
            sg.InputText(default_text=path, key=ID.INPUT_PATH,
                         **gui_utils.INPUT_DEFAULTS,
                         pad=((20, h_pad), v_pad)),
            *PATH_BUTTONS.get_buttons(common_switcher_options)
        ],
        [
            sg.Text("Title", tooltip="Text in upper left corner of each program"),
            sg.InputText(default_text=title, key=ID.INPUT_TITLE,
                         **gui_utils.INPUT_DEFAULTS,
                         pad=((32, h_pad), v_pad)),
            *TITLE_BUTTONS.get_buttons(common_switcher_options)
        ],
        [sg.Button("OK", key=ID.SUBMIT, **gui_utils.BUTTON_DEFAULTS,
                   auto_size_button=False,
                   pad=((350, 0), v_pad))]
    )
