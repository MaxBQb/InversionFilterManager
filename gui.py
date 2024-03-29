from enum import Enum
from os.path import dirname

import PySimpleGUI as sg
import inject
import requests
from natsort import os_sorted

import gui_utils as guitils
import utils
from active_window_checker import WindowInfo
from color_filter import ColorFilter
from custom_gui_elements import MultiStateButton, PageSwitchController, Switcher
from inversion_rules import InversionRule, InversionRulesController, LookForTitle, RuleType
from models.auto_update import VersionInfo


class RuleCreationWindow(guitils.BaseInteractiveWindow):
    title = guitils.get_title("create rule")
    rules_controller = inject.attr(InversionRulesController)
    color_filter = inject.attr(ColorFilter)

    class TextState(utils.StrHolder):
        PLAIN: str
        REGEX: str
        DISABLED: str

    class ID(guitils.BaseInteractiveWindow.ID):
        BUTTON_TITLE: str
        BUTTON_LOOK_FOR_TITLE: str
        BUTTON_EXCLUSIVE_RULE: str
        BUTTON_REMEMBER_PROCESSES: str
        BUTTON_PATH: str
        BUTTON_PATH_BROWSE: str
        LABEL_ERROR: str
        LABEL_TITLE: str
        LABEL_PATH: str
        LABEL_PID: str
        LABEL_OPACITY: str
        LABEL_COLOR_FILTER_TYPE: str
        FRAME_COLOR_FILTER: str
        INPUT_TITLE: str
        INPUT_PATH: str
        INPUT_PID: str
        INPUT_OPACITY: str
        INPUT_PATH_BROWSED: str
        INPUT_NAME: str
        INPUT_COLOR_FILTER_TYPE: str

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

    common_options = guitils.BUTTON_DEFAULTS | dict(
        auto_size_button=False
    )

    def __init__(self, winfo: WindowInfo):
        super().__init__()
        self.winfo = winfo
        self.path_button: MultiStateButton = None
        self.title_button: MultiStateButton = None
        self.look_for_title_button: MultiStateButton = None
        self.rule_type: MultiStateButton = None
        self.remember_processes: Switcher = None
        self.name: str = None
        self.rule: InversionRule = None
        self.path_ref = [self.winfo.path]
        self._first_color_filter_change = True

    def run(self) -> tuple[InversionRule, str]:
        self.color_filter.test_mode = True
        super().run()
        self.color_filter.test_mode = False
        return self.rule, self.name

    def init_window(self, **kwargs):
        super().init_window(element_padding=(6, 6))

    def build_layout(self):
        name = self.winfo.name.capitalize().removesuffix(".exe")
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
                ),
                LookForTitle.ROOT: dict(
                    tooltip="Use title from main (root) window",
                ),
                LookForTitle.ANY: dict(
                    tooltip="Use any title from current "
                            "to root window",
                )
            },
            self.ID.BUTTON_LOOK_FOR_TITLE,
            self.common_options,
        )
        self.rule_type = MultiStateButton(
            {
                RuleType.INCLUDE: dict(
                    tooltip="ENABLE color inversion filter if window match",
                    button_color="#FF4500",
                ),
                RuleType.EXCLUDE: dict(
                    tooltip="DISABLE color inversion filter if window match",
                    button_color="#8B0000",
                ),
                RuleType.IGNORE: dict(
                    tooltip="DON'T CHANGE color inversion filter if window match",
                    button_color="#2F4F4F",
                ),
            },
            self.ID.BUTTON_EXCLUSIVE_RULE,
            self.common_options,
        )
        self.remember_processes = Switcher(
            dict(
                tooltip="Remember process if rule applies,\n"
                        "then acts as if each window of this process\n"
                        "corresponds this rule",
                button_text="REMEMBER",
                button_color="#FF4500",
            ),
            dict(
                tooltip="Skip process matching",
                button_text="DISABLED",
                button_color="#2F4F4F",
            ),
            self.ID.BUTTON_REMEMBER_PROCESSES,
            self.common_options,
        )
        label_options = dict(
            auto_size_text=False,
            size=(7, 1)
        )
        filters = list(self.color_filter.filters_holder.filters.keys())
        self.layout = [
            [guitils.center(sg.Text(
                "Here you can choose app, "
                "windows of which will cause inversion"
            ))],
            [sg.pin(sg.Text(
                "This name already exists!",
                text_color="gold",
                visible=False,
                key=self.ID.LABEL_ERROR
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
                    **guitils.INPUT_DEFAULTS
                ),
                self.rule_type.button,
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
                    **guitils.INPUT_DEFAULTS
                ),
                self.path_button.button,
                sg.InputText(
                    key=self.ID.INPUT_PATH_BROWSED,
                    enable_events=True,
                    disabled=True,
                    visible=False
                ),
                sg.Button(
                    image_filename=utils.app_abs_path("img/browse.png"),
                    tooltip="Browse path (will overwrite current path)",
                    **guitils.ICON_BUTTON_DEFAULTS(),
                    button_type=sg.BUTTON_TYPE_BROWSE_FILE,
                    target=(sg.ThisRow, -1),
                    initial_folder=utils.alternative_path(dirname(self.winfo.path)),
                    key=self.ID.BUTTON_PATH_BROWSE,
                    **guitils.BUTTON_DEFAULTS
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
                    **guitils.INPUT_DEFAULTS
                ),
                self.title_button.button,
                self.look_for_title_button.button,
            ],
            [
                sg.Text(
                    "PID",
                    key=self.ID.LABEL_PID,
                    **label_options
                ),
                sg.InputText(
                    tooltip="Process ID (Read only)",
                    default_text=self.winfo.pid,
                    key=self.ID.INPUT_PID,
                    disabled=True,
                    **guitils.INPUT_DEFAULTS
                ),
                self.remember_processes.button,
            ],
            [
                sg.pin(sg.Column(
                    key=self.ID.FRAME_COLOR_FILTER,
                    pad=(0, 0),
                    layout=[
                        [
                            sg.Text(
                                "Opacity",
                                key=self.ID.LABEL_OPACITY,
                                **label_options,
                            ),
                            sg.Slider(
                                range=(0.0, 1.0),
                                resolution=0.01,
                                orientation='h',
                                tick_interval=0.1,
                                default_value=1.0,
                                enable_events=True,
                                size=(56, 15),
                                tooltip="Power of effect applied",
                                key=self.ID.INPUT_OPACITY,
                            ),
                        ],
                        [
                            sg.Text(
                                "Filter",
                                key=self.ID.LABEL_COLOR_FILTER_TYPE,
                                **label_options,
                            ),
                            sg.DropDown(
                                values=filters,
                                default_value=filters[0],
                                enable_events=True,
                                tooltip="Color filter type: effect to apply",
                                key=self.ID.INPUT_COLOR_FILTER_TYPE,
                                **guitils.DROPDOWN_DEFAULTS
                            ),
                        ],
                    ]
                ))
            ],
        ]

    def dynamic_build(self):
        self._inputs += [
            self.ID.INPUT_TITLE,
            self.ID.INPUT_PATH,
            self.ID.INPUT_PID,
            self.ID.INPUT_NAME,
        ]
        super().dynamic_build()

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
            self.rule_type.key,
            self.rule_type.event_handler
        )
        self.add_event_handlers(
            self.remember_processes.key,
            self.remember_processes.event_handler
        )
        self.add_event_handlers(
            self.ID.INPUT_PATH_BROWSED,
            self.on_browse_path
        )
        self.add_event_handlers(
            self.ID.INPUT_OPACITY,
            self.on_opacity_change
        )
        self.add_event_handlers(
            self.ID.INPUT_COLOR_FILTER_TYPE,
            self.on_filter_type_change
        )
        self.add_event_handlers(
            self.rule_type.key,
            self.on_type_changed
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
            utils.alternative_path(dirname(path))
        path = normpath(path)
        self.path_ref[0] = path
        window[self.ID.INPUT_PATH].update(path)
        guitils.set_underline(
            window[self.ID.LABEL_PATH],
            False
        )

    def on_opacity_change(self, event: str, window: sg.Window, values):
        if self._first_color_filter_change:
            self._first_color_filter_change = False
            self.on_filter_type_change(event, window, values)
        self.color_filter.update_opacity(values[self.ID.INPUT_OPACITY])

    def on_filter_type_change(self, event: str, window: sg.Window, values):
        self.color_filter.set_filter(
            values[self.ID.INPUT_COLOR_FILTER_TYPE],
            values[self.ID.INPUT_OPACITY],
            True
        )

    def on_submit(self, event: str, window: sg.Window, values):
        self.name = values[self.ID.INPUT_NAME]

        if self.name in self.rules_controller.rules:
            window[self.ID.LABEL_ERROR].update(visible=True)
            return

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
            self.rule_type.selected,
            self.remember_processes.selected,
            values[self.ID.INPUT_COLOR_FILTER_TYPE],
            values[self.ID.INPUT_OPACITY],
        )
        self.close()

    def on_type_changed(self, event: str, window: sg.Window, values):
        window[self.ID.FRAME_COLOR_FILTER].update(
            visible=self.rule_type.selected == RuleType.INCLUDE
        )

    def get_toggle_escape_handler(self,
                                  switcher: MultiStateButton,
                                  input_id: str):
        def on_button_switched(event: str,
                               window: sg.Window,
                               values):
            window[input_id].update(utils.change_escape(
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
            current_value = utils.change_escape(regex, False)
            if current_value != default_value[0]:
                current_value += '\n' + default_value[0]
            test_regex(regex, current_value)

        def on_regex_selected(event: str,
                              window: sg.Window,
                              values):
            guitils.set_underline(
                window[label_id],
                switcher.selected == self.TextState.REGEX
            )
        return on_text_clicked, on_regex_selected


class RuleRemovingWindow(guitils.BaseInteractiveWindow):
    all_rules = inject.attr(InversionRulesController)
    title = guitils.get_title("remove rules")

    class ID(guitils.BaseInteractiveWindow.ID):
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

        common_switcher_options = guitils.BUTTON_DEFAULTS | dict(
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
            [*self.pages.get_controls(guitils.BUTTON_DEFAULTS | dict(
                pad=pad
            ))]
        ]

    def build_rule_selection_buttons(self, common_switcher_options) -> list[sg.Button]:
        rule_buttons = []
        h_pad, v_pad = common_switcher_options['pad']
        for i, name in enumerate(self.rules):
            self.description_button_keys.append(guitils.join_id(self.ID.DESCRIPTION, str(i)))
            rule_buttons.append(
                sg.Button(
                    utils.ellipsis_trunc(name, width=10),
                    font=("Consolas", 10),
                    **(common_switcher_options |
                       dict(pad=((h_pad * 2, h_pad), v_pad))),
                    key=self.description_button_keys[-1],
                    metadata=name
                )
            )
            self.remove_rule_buttons.append(Switcher(
                *self.BUTTON_OPTIONS,
                guitils.join_id(self.ID.BUTTON_REMOVE_RULE, str(i)),
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


class RuleDescriptionWindow(guitils.BaseNonBlockingWindow):
    title = guitils.get_title("rule info")

    class ID(guitils.BaseNonBlockingWindow.ID):
        INPUT: str

    def __init__(self, rule: InversionRule, name: str):
        super().__init__()
        self.rule = rule
        self.name = name

    def build_layout(self):
        self.layout, self._inputs = guitils.layout_from_fields(
            dict(name=self.name) | {
                k: str(v) if not isinstance(v, Enum) else v.name
                for k, v in utils.public_fields(self.rule)
                if v
            },
            self.ID.INPUT
        )


class UpdateRequestWindow(guitils.ConfirmationWindow):
    title = guitils.get_title("new release is out!")

    class ID(guitils.ConfirmationWindow.ID):
        INPUT: str
        BUTTON_RELEASE_DESCRIPTION: str
        BUTTON_CHANGELOG: str

    def __init__(self, version: VersionInfo):
        super().__init__("Do you want to install new release?")
        self.version = version

    def build_layout(self):
        import _meta as app
        from hurry.filesize import size, alternative

        self.layout = [
            [guitils.center(
                sg.Text(
                    'Update info',
                    font=("Verdana", 18)
                ),
            )]
        ]

        if app.__developer_mode__:
            self.layout.append([guitils.center(sg.Text(
                'ATTENTION, YOU ARE IN DEVELOPER MODE',
                font=("Tahoma", 16, 'bold'),
                text_color='gold',
                tooltip=
                "You started this program from .py file\n"
                "Run program from source codes needs only for developers\n"
                "Normal users run program from .exe file\n"
                "Note, that if you perform update, the normal .exe version\n"
                "of program will override your project"
            ))])

        description = dict(
            app_name=app.__product_name__,
            current_version=app.__version__,
            latest_version=self.version.version_text,
            release_size=size(self.version.release_info.size, alternative),
        )
        label_size = (utils.max_len(description.keys()) + 1, 1)
        input_size = (utils.max_len(description.values()) + 4, 1)
        font = guitils.INPUT_DEFAULTS['font']
        self._inputs = [
            guitils.join_id(self.ID.INPUT, name)
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
                 **guitils.INPUT_DEFAULTS
             )]
            for (label, content), input_key in zip(description.items(), self._inputs)
        ]
        self.layout += [[guitils.center(
            sg.Button(
                "Release description",
                key=self.ID.BUTTON_RELEASE_DESCRIPTION,
                **guitils.BUTTON_DEFAULTS
            ),
            sg.Button(
                "Changelog",
                key=self.ID.BUTTON_CHANGELOG,
                **guitils.BUTTON_DEFAULTS
            ),
        )]]
        super().build_layout()

    def set_handlers(self):
        super().set_handlers()
        self.add_event_handlers(
            self.ID.BUTTON_RELEASE_DESCRIPTION,
            self.show_release_description,
        )
        self.add_event_handlers(
            self.ID.BUTTON_CHANGELOG,
            self.show_changelog,
        )

    def show_release_description(self, event, window, values):
        self._open_dependent_window(guitils.OutputWindow(
            self.version.description, f"Release {self.version.version_text} Description"
        ))

    def show_changelog(self, event, window, values):
        import _meta as app
        link = "https://raw.githubusercontent.com/MaxBQb/InversionFilterManager/master/CHANGELOG.md"
        self._open_dependent_window(guitils.OutputWindow(
            requests.get(link).text, f"Changelog (current version {app.__version__})"
        ))


class ChooseRuleCandidateWindow(guitils.BaseInteractiveWindow):
    title = guitils.get_title("select rule candidate")

    class ID(guitils.BaseInteractiveWindow.ID):
        DESCRIPTION: str
        LIST_NAMES: str

    def __init__(self, windows_info: list[WindowInfo]):
        super().__init__()
        self.windows_info = windows_info
        self.selected_window = windows_info[0]
        self.chosen_window: WindowInfo = None
        self.name_to_winfo_map = dict()
        self.property_to_id_map = dict()

    def run(self) -> WindowInfo:
        super().run()
        return self.chosen_window

    @staticmethod
    def _get_name(winfo):
        name = utils.ellipsis_trunc(winfo.name, 18)
        title = utils.ellipsis_trunc(winfo.title, 18)
        if title:
            return f"{name} '{title}'"
        return name

    def build_layout(self):
        self.name_to_winfo_map = {
            self._get_name(winfo): winfo
            for winfo in self.windows_info
        }
        names = list(self.name_to_winfo_map.keys())
        name_max_len = utils.max_len(names) + 1
        self.layout += [
            [sg.Listbox(
                names,
                select_mode=sg.LISTBOX_SELECT_MODE_BROWSE,
                default_values=[names[0]],
                font=guitils.INPUT_DEFAULTS["font"],
                size=(name_max_len, 3),
                enable_events=True,
                key=self.ID.LIST_NAMES,
                **guitils.LIST_BOX_DEFAULTS,
            )],
        ]

        max_text_len = max(
            utils.max_len(
                str(v) for k, v in utils.public_fields(winfo)
            )
            for winfo in self.windows_info
        )
        max_text_len = utils.set_between(20, 40, max_text_len + 1)
        layout, self._inputs = guitils.layout_from_fields(
            utils.public_fields(self.selected_window),
            self.ID.DESCRIPTION,
            content_kwargs=dict(size=(max_text_len, 1))
        )
        self.layout += layout
        self.property_to_id_map = {
            k: input_id
            for input_id, (k, v) in zip(
                self._inputs,
                utils.public_fields(self.selected_window)
            )
        }

    def set_handlers(self):
        super().set_handlers()
        self.add_event_handlers(
            self.ID.LIST_NAMES,
            self.update_info
        )

    def update_info(self,
                    event: str,
                    window: sg.Window,
                    values):
        winfo = self.name_to_winfo_map[values[event][0]]
        self.selected_window = winfo
        for field, value in utils.public_fields(winfo):
            input_id = self.property_to_id_map.get(field)
            if input_id is not None:
                window[input_id].update(str(value))

    def init_window(self, **kwargs):
        super().init_window(
            element_justification='center',
        )

    def dynamic_build(self):
        self.update_info(self.ID.LIST_NAMES, self.window, {
            self.ID.LIST_NAMES: [self._get_name(self.selected_window)]
        })
        self.window[self.ID.LIST_NAMES].set_focus()
        super().dynamic_build()

    def on_submit(self,
                  event: str,
                  window: sg.Window,
                  values):
        self.chosen_window = self.selected_window
        self.close()


class ChooseRemoveCandidateWindow(ChooseRuleCandidateWindow):
    title = guitils.get_title("select window -> remove rules")

    def build_layout(self):
        self.layout = [
            [sg.Text("Choose window, then you'll be "
                     "able to remove rules associated with it")],
            [sg.Text("To select active window, and skip this "
                     "dialog,\nuse  [ Ctrl Alt - ]  hotkey "
                     "in any place", text_color="gold",
                     pad=(0, 0))]
        ]
        super().build_layout()


class ChooseAppendCandidateWindow(ChooseRuleCandidateWindow):
    title = guitils.get_title("select window -> create rule")

    def build_layout(self):
        self.layout = [
            [sg.Text("Choose window, then you'll be "
                     "able to create rule associated with it")],
            [sg.Text("To select active window, and skip this "
                     "dialog,\nuse  [ Ctrl Alt + ]  hotkey "
                     "in any place", text_color="gold",
                     pad=(0, 0))]
        ]
        super().build_layout()


def test_regex(regex: str, text: str):
    from urllib.parse import urlencode
    import webbrowser
    webbrowser.open('https://regex101.com/?' + urlencode(dict(
        flavor='python',
        regex=regex,
        testString=text
    )))
