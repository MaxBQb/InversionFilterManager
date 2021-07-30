import PySimpleGUI as sg
from gui.switching_button import ButtonSwitchController
from gui.pages import PageSwitchController
from utils import field_names_to_values, ellipsis_trunc
import gui.gui_utils as gui_utils
from natsort import os_sorted


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


WINDOW_TITLE = gui_utils.get_title("select rules")

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


def select_rules(rules: list[str]):
    actions = []
    rules = os_sorted(rules)
    rule_buttons = []
    pad = h_pad, v_pad = 6, 6
    common_switcher_options = gui_utils.BUTTON_DEFAULTS | dict(
        pad=pad,
        use_ttk_buttons=False,
        auto_size_button=False
    )
    common_action = ButtonSwitchController(
        BUTTON_OPTIONS,
        ID.COMMON_ACTION,
        common_switcher_options
    )
    for i, name in enumerate(rules):
        rule_buttons.append(
            sg.Button(
                ellipsis_trunc(name, width=10),
                font=("Consolas", 10),
                **(common_switcher_options |
                   dict(pad=((h_pad*2, h_pad), v_pad)))
            )
        )
        actions.append(
            ButtonSwitchController(
                BUTTON_OPTIONS,
                gui_utils.join_id(ID.ACTION, str(i)),
                common_switcher_options | dict(
                    metadata=name
                )
            )
        )
        rule_buttons.append(actions[-1].button)

    pages = PageSwitchController.from_list(
        rule_buttons)(key=ID.PAGES)

    window = sg.Window(WINDOW_TITLE, build_view(
       pages, common_action.button, len(rules) == 1
    ), finalize=True, element_justification='center')
    window.bring_to_front()
    gui_utils.deny_maximize(window)
    gui_utils.deny_minimize(window)
    context = {
        'remove': set()
    }
    rules_to_remove = context['remove']

    # Create an event loop
    while True:
        event, values = window.read()

        pages.handle_event(event, window)
        for action in actions:
            if action.handle_event(event, window):
                name = window[event].metadata
                if action.selected == ButtonState.REMOVE:
                    rules_to_remove.add(name)
                else:
                    rules_to_remove.remove(name)

        if common_action.handle_event(event, window):
            for action in actions:
                action.change_state(common_action.selected, window)

            if common_action.selected == ButtonState.REMOVE:
                rules_to_remove.update(rules)
            else:
                rules_to_remove.clear()

        if event == ID.SUBMIT:
            break

        if event == sg.WIN_CLOSED:
            context = None
            break

    window.close()
    if not context:
        return None
    return context


def get_key_by_state(button_switch: ButtonSwitchController, key: str):
    if button_switch.selected == ButtonState.DISABLED:
        return
    if button_switch.selected == ButtonState.REGEX:
        key += '_regex'
    return key


def build_view(pages: PageSwitchController,
               common_state_button: sg.Button,
               single_rule: bool):
    pad = 12, 12
    common_switcher_options = gui_utils.BUTTON_DEFAULTS | dict(
        pad=pad,
        auto_size_button=False
    )

    return gui_utils.create_layout(
        WINDOW_TITLE,
        [sg.Text(("Rule" if single_rule else "List of rules") +
                 " associated with this window:")],
        [sg.Text("Common state:"), common_state_button] if not single_rule else [],
        [pages.get_pages_holder()],
        [*pages.get_controls(gui_utils.BUTTON_DEFAULTS | dict(
            disabled_button_color="#21242c"
        ))],
        [sg.Button("OK", key=ID.SUBMIT,
                   **common_switcher_options)]
    )
