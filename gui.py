import PySimpleGUI as sg
from configobj import ConfigObj
from natsort import os_sorted
from active_window_checker import WindowInfo
from custom_gui_elements import MultiStateButton, PageSwitchController, Switcher
from realtime_data_sync import RulesFileManager
from utils import StrHolder, ellipsis_trunc, max_len, change_escape, alternative_path, explore
import gui_utils
from gui_utils import BaseInteractiveWindow, BaseNonBlockingWindow
import inject
from inversion_rules import InversionRule, InversionRulesController, LookForTitle
from os.path import dirname


class RuleCreationWindow(BaseInteractiveWindow):
    title = gui_utils.get_title("create rule")

    class TextState(StrHolder):
        PLAIN: str
        REGEX: str
        DISABLED: str

    class ID(BaseInteractiveWindow.ID):
        BUTTON_TITLE: str
        BUTTON_LOOK_FOR_TITLE: str
        BUTTON_EXCLUSIVE_RULE: str
        BUTTON_PATH: str
        BUTTON_PATH_BROWSE: str
        LABEL_TITLE: str
        LABEL_PATH: str
        INPUT_TITLE: str
        INPUT_PATH: str
        INPUT_PATH_BROWSED: str
        INPUT_NAME: str

    path_button_options = {
        TextState.PLAIN: dict(
            tooltip="Simply checks strings equality"
                    "\nAutomatically unescape text",
            button_color="#FF4500",
        ),
        TextState.REGEX: dict(
            tooltip="Use regex text matching (PRO)"
                    "\nAutomatically escape text",
            button_color="#8B0000",
        ),
    }

    title_button_options = {
        TextState.DISABLED: dict(
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
        self.path_button: MultiStateButton = None
        self.title_button: MultiStateButton = None
        self.look_for_title_button: MultiStateButton = None
        self.exclusive_rule: Switcher = None
        self.name: str = None
        self.rule: InversionRule = None
        self.path_ref = [self.winfo.path]

    def run(self) -> tuple[InversionRule, str]:
        super().run()
        return self.rule, self.name

    def init_window(self, **kwargs):
        super().init_window(element_padding=(6, 6))

    def build_layout(self):
        name = self.winfo.name.removesuffix(".exe").title()
        self.path_button = MultiStateButton(
            self.path_button_options,
            self.ID.BUTTON_PATH,
            self.common_options
        )
        self.title_button = MultiStateButton(
            self.title_button_options,
            self.ID.BUTTON_TITLE,
            self.common_options
        )
        self.look_for_title_button = MultiStateButton({
                LookForTitle.CURRENT: dict(
                    tooltip="Use title from current window",
                    button_text="CURRENT"
                ),
                LookForTitle.ROOT: dict(
                    tooltip="Use title from main (root) window",
                    button_text="ROOT"
                ),
                LookForTitle.ANY: dict(
                    tooltip="Use any title from current "
                            "to root window",
                    button_text="ANY"
                )
            },
            self.ID.BUTTON_LOOK_FOR_TITLE,
            self.common_options,
        )
        self.exclusive_rule = Switcher(
            dict(
                tooltip="DISABLE color inversion filter if window match",
                button_text="EXCLUDE",
                button_color="#2F4F4F",
            ),
            dict(
                tooltip="ENABLE color inversion filter if window match",
                button_text="INCLUDE",
                button_color="#FF4500",
            ),
            self.ID.BUTTON_EXCLUSIVE_RULE,
            self.common_options,
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
                self.exclusive_rule.button,
            ],
            [
                sg.Text(
                    "Path",
                    key=self.ID.LABEL_PATH,
                    tooltip='Click to test this regex\n(only when regex selected)',
                    enable_events=True,
                    **label_options
                ),
                sg.InputText(
                    tooltip="Path to program",
                    default_text=self.winfo.path,
                    key=self.ID.INPUT_PATH,
                    **gui_utils.INPUT_DEFAULTS
                ),
                self.path_button.button,
                sg.InputText(
                    key=self.ID.INPUT_PATH_BROWSED,
                    enable_events=True,
                    disabled=True,
                    visible=False
                ),
                sg.Button(
                    image_filename="./img/browse.png",
                    tooltip="Browse path (will overwrite current path)",
                    **gui_utils.ICON_BUTTON_DEFAULTS(),
                    button_type=sg.BUTTON_TYPE_BROWSE_FILE,
                    target=(sg.ThisRow, -1),
                    initial_folder=alternative_path(dirname(self.winfo.path)),
                    key=self.ID.BUTTON_PATH_BROWSE,
                    **gui_utils.BUTTON_DEFAULTS
                ),
            ],
            [
                sg.Text(
                    "Title",
                    key=self.ID.LABEL_TITLE,
                    tooltip='Click to test this regex\n(only when regex selected)',
                    enable_events=True,
                    **label_options
                ),
                sg.InputText(
                    tooltip="Text in upper left corner of each program",
                    default_text=self.winfo.title,
                    key=self.ID.INPUT_TITLE,
                    disabled=True,
                    **gui_utils.INPUT_DEFAULTS
                ),
                self.title_button.button,
                self.look_for_title_button.button,
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
        title_label_clicked, title_button_clicked = self.get_regex_open_test_handlers(
            self.title_button,
            self.ID.LABEL_TITLE,
            self.ID.INPUT_TITLE,
            [self.winfo.title]
        )
        path_label_clicked, path_button_clicked = self.get_regex_open_test_handlers(
            self.path_button,
            self.ID.LABEL_PATH,
            self.ID.INPUT_PATH,
            self.path_ref
        )
        self.add_event_handlers(
            self.title_button.key,
            self.title_button.event_handler,
            self.disable_title,
            self.get_toggle_escape_handler(
                self.title_button,
                self.ID.INPUT_TITLE
            ),
            title_button_clicked
        )
        self.add_event_handlers(
            self.ID.LABEL_TITLE,
            title_label_clicked
        )
        self.add_event_handlers(
            self.ID.LABEL_PATH,
            path_label_clicked
        )
        self.add_event_handlers(
            self.path_button.key,
            self.path_button.event_handler,
            self.get_toggle_escape_handler(
                self.path_button,
                self.ID.INPUT_PATH
            ),
            path_button_clicked
        )
        self.add_event_handlers(
            self.look_for_title_button.key,
            self.look_for_title_button.event_handler
        )
        self.add_event_handlers(
            self.exclusive_rule.key,
            self.exclusive_rule.event_handler
        )
        self.add_event_handlers(
            self.ID.INPUT_PATH_BROWSED,
            self.on_browse_path
        )

    def disable_title(self, event: str, window: sg.Window, values):
        window[self.ID.INPUT_TITLE].update(
            disabled=self.title_button.selected ==
                     self.TextState.DISABLED
        )

    def on_browse_path(self,
                       event: str,
                       window: sg.Window,
                       values):
        from os.path import normpath
        if self.path_button.selected == self.TextState.REGEX:
            self.path_button.event_handler(event, window, values)
        path = values[self.ID.INPUT_PATH_BROWSED]
        window[self.ID.BUTTON_PATH_BROWSE].InitialFolder = \
            alternative_path(dirname(path))
        path = normpath(path)
        self.path_ref[0] = path
        window[self.ID.INPUT_PATH].update(path)
        gui_utils.set_underline(
            window[self.ID.LABEL_PATH],
            False
        )

    def on_submit(self, event: str, window: sg.Window, values):
        def get_keys(button, key):
            value = values[key]
            return {
                self.TextState.DISABLED: (None, None),
                self.TextState.REGEX: (None, value),
                self.TextState.PLAIN: (value, None),
            }.get(button.selected)

        self.rule = InversionRule(
            *get_keys(self.path_button, self.ID.INPUT_PATH),
            *get_keys(self.title_button, self.ID.INPUT_TITLE),
            self.look_for_title_button.selected,
            self.exclusive_rule.selected
        )
        self.name = values[self.ID.INPUT_NAME]
        self.close()

    def get_toggle_escape_handler(self,
                                  switcher: MultiStateButton,
                                  input_id: str):
        def on_button_switched(event: str,
                               window: sg.Window,
                               values):
            window[input_id].update(change_escape(
                values[input_id],
                switcher.selected == self.TextState.REGEX
            ))
        return on_button_switched

    def get_regex_open_test_handlers(self,
                                     switcher: MultiStateButton,
                                     label_id: str,
                                     input_id: str,
                                     default_value: list[str]):
        def on_text_clicked(event: str,
                            window: sg.Window,
                            values):
            if switcher.selected != self.TextState.REGEX:
                return
            regex = values[input_id]
            current_value = change_escape(regex, False)
            if current_value != default_value[0]:
                current_value += '\n' + default_value[0]
            test_regex(regex, current_value)

        def on_regex_selected(event: str,
                              window: sg.Window,
                              values):
            gui_utils.set_underline(
                window[label_id],
                switcher.selected == self.TextState.REGEX
            )
        return on_text_clicked, on_regex_selected


class RuleRemovingWindow(BaseInteractiveWindow):
    all_rules = inject.attr(InversionRulesController)
    title = gui_utils.get_title("select rules")

    class ID(BaseInteractiveWindow.ID):
        BUTTON_REMOVE_RULE: str
        BUTTON_REMOVE_ALL_RULES: str
        DESCRIPTION: str
        PAGES: str

    BUTTON_OPTIONS = (
        dict(
            tooltip="Remove this rule",
            button_color="#8B0000",
            button_text="REMOVE"
        ),
        dict(
            tooltip="Preserve this rule",
            button_color="#2F4F4F",
            button_text="SKIP"
        ),
    )

    def __init__(self, rules: list[str]):
        super().__init__()
        self.rules = os_sorted(rules)
        self.description_button_keys: list[str] = []
        self.remove_rule_buttons: list[Switcher] = []
        self.remove_all_rules_button: Switcher = None
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

        self.remove_all_rules_button = Switcher(
            *self.BUTTON_OPTIONS,
            self.ID.BUTTON_REMOVE_ALL_RULES,
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
            [sg.Text("Common state:", pad=(0, 0)), self.remove_all_rules_button.button] if not single_rule else [],
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
            self.remove_rule_buttons.append(Switcher(
                *self.BUTTON_OPTIONS,
                gui_utils.join_id(self.ID.BUTTON_REMOVE_RULE, str(i)),
                common_switcher_options | dict(
                    metadata=name
                )
            ))
            rule_buttons.append(self.remove_rule_buttons[-1].button)
        return rule_buttons

    def set_handlers(self):
        super().set_handlers()
        for button in self.remove_rule_buttons:
            self.add_event_handlers(
                button.key,
                button.event_handler
            )
        for key in self.description_button_keys:
            self.add_event_handlers(
                key,
                self.on_description_open
            )
        self.description_button_keys = None
        self.add_event_handlers(
            self.remove_all_rules_button.key,
            self.remove_all_rules_button.event_handler,
            self.on_remove_all_click
        )

    def init_window(self, **kwargs):
        super().init_window(
            element_justification='center'
        )

    def on_remove_all_click(self,
                            event: str,
                            window: sg.Window,
                            values):
        for button in self.remove_rule_buttons:
            button.change_state(
                self.remove_all_rules_button.selected,
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
            window[button.key].metadata
            for button in self.remove_rule_buttons
            if button.selected
        }
        self.close()


class RuleDescriptionWindow(BaseNonBlockingWindow):
    title = gui_utils.get_title("rule info")

    class ID(BaseNonBlockingWindow.ID):
        INPUT: str

    def __init__(self, rule: InversionRule, name: str):
        super().__init__()
        self.rule = rule
        self.name = name
        self.inputs: list[str] = None

    def build_layout(self):
        description = dict(
            name=self.name,
        ) | {
            k: str(v) for k, v in vars(self.rule).items()
            if not k.startswith('_') and v
        }
        size = (max_len(description.keys()), 1)
        font = gui_utils.INPUT_DEFAULTS['font']
        self.inputs = [
            gui_utils.join_id(self.ID.INPUT, name)
            for name in description
        ]
        self.layout = [[
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
                **gui_utils.INPUT_DEFAULTS
            )
            ] for (label, content), input_key
              in zip(description.items(), self.inputs)
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
        label_size = (max_len(description.keys()) + 1, 1)
        input_size = (max_len(description.values()) + 4, 1)
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


def test_regex(regex: str, text: str):
    from urllib.parse import urlencode
    import webbrowser
    webbrowser.open('https://regex101.com/?' + urlencode(dict(
        flavor='python',
        regex=regex,
        testString=text
    )))


class Tray:
    config = inject.attr(ConfigObj)
    rules_file_manager = inject.attr(RulesFileManager)

    def __init__(self):
        from pystray import Icon
        self.tray: Icon = None

    def run(self):
        from _meta import __product_name__
        from pystray import Icon
        from PIL import Image
        self.tray = Icon(
            __product_name__,
            Image.open("img/inversion_manager.ico"),
            menu=self.build_menu()
        ).run()

    def close(self):
        self.tray.shutdown()

    def build_menu(self):
        from pystray import Menu, MenuItem
        import _meta as app

        def _open(path):
            def __open(*ignore):
                explore(path)
            return __open

        return Menu(
            MenuItem(
                f'{app.__product_name__} v{app.__version__}',
                None, enabled=False),
            Menu.SEPARATOR,
            MenuItem(
                '&Open',
                Menu(
                    MenuItem('&Work directory', _open(".")),
                    MenuItem('&Config file', _open(self.config.filename)),
                    MenuItem('&Inversion rules file', _open(self.rules_file_manager.filename))
                )
            ),
            Menu.SEPARATOR,
            MenuItem('&Add app to inversion rules', None),
            MenuItem('&Remove app from inversion rules', None),
            Menu.SEPARATOR,
            MenuItem('Check for &updates', None),
            Menu.SEPARATOR,
            MenuItem('&Quit', None),
        )