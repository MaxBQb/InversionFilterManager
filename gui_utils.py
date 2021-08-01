import PySimpleGUI as sg
from typing import Callable, Any
from _meta import __product_name__ as app_name
from utils import field_names_to_values

BUTTON_DEFAULTS = dict(
    mouseover_colors="#333333",
    use_ttk_buttons=True,
    disabled_button_color="#21242c"
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


def join_id(id_: str, *id_parts: str):
    return id_ + '-'.join(id_parts) + '-'


def center(element):
    return sg.Column([[element]],
                     pad=(0, 0),
                     justification='center')


class BaseInteractiveWindow:
    HANDLER = Callable[[str, sg.Window, Any], None]

    title = get_title("base window")

    @field_names_to_values("-{}-")
    class ID:
        SUBMIT: str

    id = ID()

    def __init__(self):
        self.window: sg.Window = None
        self.event_handlers: dict[str, list[BaseInteractiveWindow.HANDLER]] = {}
        self.is_running = False
        self.layout: list[list] = None

    def run(self) -> Any:
        """
        Should be used to open window
        """
        self.build_layout()
        self.add_title()
        self.add_submit_button()
        self.set_handlers()
        self.init_window()
        self.setup_window()
        self.dispatch_events()

    def build_layout(self):
        self.layout = [[]]

    def add_title(self, **kwargs):
        self.layout.insert(0, [sg.Titlebar(
            title=self.title,
            **kwargs
        )])

    def add_submit_button(self, **kwargs):
        self.layout.append([center(sg.Button(
            key=self.id.SUBMIT,
            **(BUTTON_DEFAULTS | dict(
                button_text="OK",
                pad=(6, 6),
                auto_size_button=False
            ) | kwargs)
        ))])

    def close(self):
        self.is_running = False

    def init_window(self, **kwargs):
        self.window = sg.Window(
            self.title,
            self.layout,
            **(dict(
                finalize=True,
                element_padding=(12, 12),
                disable_minimize=True,
            ) | kwargs)
        )

    def setup_window(self):
        self.window.bring_to_front()
        deny_maximize(self.window)
        deny_minimize(self.window)

    def set_handlers(self):
        self.add_event_handlers(
            sg.WIN_CLOSED,
            self.make_handler(self.close)
        )
        self.add_event_handlers(
            self.id.SUBMIT,
            self.on_submit
        )

    def run_event_loop(self):
        self.is_running = True
        while self.is_running:
            yield self.window.read()
        self.window.close()

    def dispatch_events(self):
        default_handler = [self.on_unhandled_event]
        for event, values in self.run_event_loop():
            handlers = self.event_handlers.get(event, default_handler)
            for handler in handlers:
                handler(event, self.window, values)

    def on_unhandled_event(self,
                           event: str,
                           window: sg.Window,
                           values):
        pass

    def on_submit(self, event: str, window: sg.Window, values):
        self.close()

    def add_event_handlers(self, event: str, *handlers: HANDLER):
        if event not in self.event_handlers:
            self.event_handlers[event] = handlers
        else:
            self.event_handlers[event] += handlers

    @staticmethod
    def make_handler(func) -> HANDLER:
        return lambda e, w, v: func()
