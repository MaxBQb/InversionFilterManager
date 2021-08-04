import PySimpleGUI as sg
from typing import Callable, Any
from _meta import __product_name__ as app_name
from utils import StrHolder


BUTTON_DEFAULTS = dict(
    mouseover_colors="#333333",
    disabled_button_color="#21242c",
)

INPUT_DEFAULTS = dict(
    disabled_readonly_background_color="#222",
    font=('Consolas', 12)
)

INPUT_EXTRA_DEFAULTS = dict(
    insertwidth='4',
    insertbackground='silver',
    selectbackground='#175924',
    selectforeground='silver',
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


def center(*elements):
    return sg.Column([list(elements)],
                     pad=(0, 0),
                     justification='center')


class BaseNonBlockingWindow:
    title = get_title("base non-blocking window")

    class ID(StrHolder):
        @staticmethod
        def _get_value(field_name: str) -> str:
            return f"-{field_name}-"

        SUBMIT: str

    def __init__(self):
        self.window: sg.Window = None
        self.layout: list[list] = []
        self.dependent_windows = set()

    def _add_dependency(self, dependent_window):
        self.dependent_windows.add(dependent_window)

    def _open_dependent_window(self, dependent_window):
        self._add_dependency(dependent_window)
        return dependent_window.run()

    def _close_dependent(self):
        for dependent in self.dependent_windows:
            dependent.close()

    def run(self):
        """
        Should be used to open window
        """
        self.build_layout()
        self.add_title()
        self.add_submit_button()
        self.init_window()
        self.dynamic_build()

    def build_layout(self):
        self.layout = [[]]

    def add_title(self, **kwargs):
        self.layout.insert(0, [sg.Titlebar(
            title=self.title,
            **kwargs
        )])

    def add_submit_button(self, **kwargs):
        self.layout.append([center(sg.Button(
            key=self.ID.SUBMIT,
            **(BUTTON_DEFAULTS | dict(
                button_text="OK",
                pad=(6, 6),
                auto_size_button=False,
                button_type=sg.BUTTON_TYPE_CLOSES_WIN_ONLY
            ) | kwargs)
        ))])

    def close(self):
        self._close_dependent()
        self.window.close()

    def init_window(self, **kwargs):
        self.window = sg.Window(
            self.title,
            self.layout,
            **(dict(
                finalize=True,
                element_padding=(12, 12),
                keep_on_top=True,
                grab_anywhere=True,
            ) | kwargs)
        )

    def dynamic_build(self):
        self.setup_window()

    def setup_window(self):
        deny_maximize(self.window)
        deny_minimize(self.window)


class BaseInteractiveWindow(BaseNonBlockingWindow):
    HANDLER = Callable[[str, sg.Window, Any], None]

    title = get_title("base window")

    def __init__(self):
        super().__init__()
        self.event_handlers: dict[str, list[BaseInteractiveWindow.HANDLER]] = {}
        self.is_running = False

    def run(self) -> Any:
        """
        Should be used to open window
        """
        self.build_layout()
        self.add_title()
        self.add_submit_button()
        self.set_handlers()
        self.init_window()
        self.dynamic_build()
        self.dispatch_events()

    def add_submit_button(self, **kwargs):
        super().add_submit_button(
            button_type=sg.BUTTON_TYPE_READ_FORM
        )

    def close(self):
        self.is_running = False
        self._close_dependent()

    def set_handlers(self):
        self.add_event_handlers(
            sg.WIN_CLOSED,
            self.make_handler(self.close)
        )
        self.add_event_handlers(
            self.ID.SUBMIT,
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
            self.event_handlers[event] = list(handlers)
        else:
            self.event_handlers[event] += handlers

    @staticmethod
    def make_handler(func) -> HANDLER:
        return lambda e, w, v: func()


class ConfirmationWindow(BaseInteractiveWindow):
    title = get_title("confirm")

    class ID(BaseInteractiveWindow.ID):
        CANCEL: str

    def __init__(self, question: str, default: bool = False):
        super().__init__()
        self.question = question
        self.positive_answer = default

    def build_layout(self):
        self.layout.append([center(sg.Text(self.question))])

    def run(self) -> bool:
        super().run()
        return self.positive_answer

    def add_submit_button(self, yes_kwargs: dict = {}, no_kwargs: dict = {}, **common):
        common_options = BUTTON_DEFAULTS | dict(
            pad=(6, 6),
            auto_size_button=False,
            button_type=sg.BUTTON_TYPE_READ_FORM
        ) | common

        yes_kwargs = common_options | dict(
            button_text="Yes",
            button_color="#555"
        ) | yes_kwargs

        no_kwargs = common_options | dict(
            button_text="No",
            button_color="#333"
        ) | no_kwargs

        get_text = lambda d: d.get('button_text', '')
        size = (len(max((
            get_text(common_options),
            get_text(no_kwargs),
            get_text(yes_kwargs),
        ), key=len)) + 2, 1)

        self.layout.append([center(
            sg.Button(
                key=self.ID.SUBMIT,
                size=size,
                **yes_kwargs
            ),
            sg.Button(
                key=self.ID.CANCEL,
                size=size,
                **no_kwargs
            ),
        )])

    def set_handlers(self):
        super().set_handlers()
        self.add_event_handlers(
            self.ID.CANCEL,
            self.on_cancel
        )

    def on_submit(self,
                  event: str,
                  window: sg.Window,
                  values):
        self.positive_answer = True
        self.close()

    def on_cancel(self,
                  event: str,
                  window: sg.Window,
                  values):
        self.positive_answer = False
        self.close()
