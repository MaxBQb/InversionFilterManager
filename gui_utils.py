import math
from typing import Callable, Any

import PySimpleGUI as sg

import gui_utils
from _meta import __product_name__ as app_name
from utils import StrHolder, max_len, app_abs_path, set_between

BUTTON_DEFAULTS = dict(
    mouseover_colors="#333333",
    disabled_button_color="#21242c",
)

LIST_BOX_DEFAULTS = dict(
    background_color="#313131",
    no_scrollbar=True,
    highlight_background_color="#515151",
    highlight_text_color="#cecece",
)

ICON_BUTTON_DEFAULTS = lambda: dict(
    button_color=(sg.theme_background_color(), sg.theme_background_color()),
    border_width=0,
)

INPUT_DEFAULTS = dict(
    disabled_readonly_background_color="#222",
    font=('Consolas', 12)
)

DROPDOWN_DEFAULTS = dict(
    button_background_color="#313131",
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
    sg.set_options(
        titlebar_icon=app_abs_path("img/inversion_manager.png"),
        titlebar_font=("Tahoma", 12),
        icon=app_abs_path("img/inversion_manager.png"),
    )


def get_title(title: str):
    return f"{app_name}: {title.title()}"


def hide(window, key: str):
    window[key].update(visible=False)


def set_underline(label: sg.Text, underline=True):
    label.update(font=(
        (*label.Font, 'underline')
        if underline
        else label.Font[:2]
    ))


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


def layout_from_fields(fields, base_key="-INPUT-", content_kwargs={}):
    description = dict(fields)
    size = (max_len(description.keys())+1, 1)
    font = INPUT_DEFAULTS['font']
    inputs = [
        join_id(base_key, name)
        for name in description
    ]
    layout = [[
            sg.Text(
                label.capitalize().replace('_', ' ') + ':',
                auto_size_text=False,
                font=font,
                size=size,
            ),
            sg.InputText(
                content,
                readonly=True,
                key=input_key,
                **INPUT_DEFAULTS,
                **content_kwargs
            )
        ]
        for (label, content), input_key
        in zip(description.items(), inputs)
    ]
    return layout, inputs


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
        self.dependent_windows: set[BaseNonBlockingWindow] = set()
        # Applies default input style
        self._inputs: list[str] = []

    def _add_dependency(self, dependent_window):
        self.dependent_windows.add(dependent_window)

    def _open_dependent_window(self, dependent_window):
        self._add_dependency(dependent_window)
        return dependent_window.run()

    def _close_dependent(self):
        for dependent in self.dependent_windows:
            dependent.send_close_event()

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
                bind_return_key=True,
                auto_size_button=False,
                button_type=sg.BUTTON_TYPE_CLOSES_WIN_ONLY
            ) | kwargs)
        ))])

    def close(self):
        self._close_dependent()
        self.window.close()

    def send_close_event(self):
        if not self.window.was_closed():
            self.close()

    def init_window(self, **kwargs):
        self.window = sg.Window(
            self.title,
            self.layout,
            **(dict(
                finalize=True,
                alpha_channel=0,
                element_padding=(12, 12),
                keep_on_top=True,
                grab_anywhere=True,
            ) | kwargs)

        )

    def dynamic_build(self):
        self.setup_window()
        for key in self._inputs:
            self.window[key].Widget.config(
                **INPUT_EXTRA_DEFAULTS
            )
        self._inputs = None
        self.window.alpha_channel = 1

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

    def send_close_event(self):
        if not self.window.was_closed():
            self.window.write_event_value(sg.WIN_CLOSED, None)

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
            button_color="#555",
            bind_return_key=self.positive_answer,
        ) | yes_kwargs

        no_kwargs = common_options | dict(
            button_text="No",
            button_color="#333",
            bind_return_key=not self.positive_answer,
        ) | no_kwargs

        get_text = lambda d: d.get('button_text', '')
        size = (max_len((
            get_text(common_options),
            get_text(no_kwargs),
            get_text(yes_kwargs),
        )) + 2, 1)

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


class OutputWindow(BaseNonBlockingWindow):
    def __init__(self, message: str, title="note"):
        self.title = get_title(title)
        self.message = message.strip()
        super().__init__()

    def build_layout(self):
        lines = self.message.split('\n')
        longest_line_length = len(max(lines, key=len))
        width = set_between(20, 80, longest_line_length)
        lines_count = sum(
            math.ceil(len(line) / float(width)) for line in lines
        )
        height = set_between(5, 25, lines_count)
        self.layout.append([center(
            sg.Multiline(
                self.message,
                autoscroll=True,
                disabled=True,
                font=gui_utils.INPUT_DEFAULTS['font'],
                size=(width, height),
                no_scrollbar=height >= lines_count
            )
        )])
