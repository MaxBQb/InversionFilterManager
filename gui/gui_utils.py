import PySimpleGUI as sg
from _meta import __product_name__ as app_name


BUTTON_DEFAULTS = dict(
    mouseover_colors="#333333",
    use_ttk_buttons=True,
)

INPUT_DEFAULTS = dict(
    disabled_readonly_background_color="#222",
)


def init_theme():
    sg.theme("DarkGray13")


def get_title(title: str):
    return f"{app_name}: {title.title()}"


def create_layout(title: str, *rows):
    return [
        [sg.Titlebar(title=title)],
        *rows
    ]


def hide(window, key: str):
    window[key].update(visible=False)


def deny_maximize(window):
    '''
    Apply on custom titlebar only
    '''
    hide(window, sg.TITLEBAR_MAXIMIZE_KEY)


def deny_minimize(window):
    '''
    Apply on custom titlebar only
    '''
    hide(window, sg.TITLEBAR_MINIMIZE_KEY)


def join_id(*ids: str):
    return '-'.join(ids)


def center(element):
    return sg.Column([[element]],
                     pad=(0, 0),
                     justification='center')
