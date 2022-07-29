from collections import OrderedDict
from typing import TextIO

import inject
import win_magnification as mag  # type: ignore

from app_close import AppCloseManager
from file_tracker import Syncable, DataFileSyncer
from main_thread_loop import execute_in_main_thread

COLOR_FILTERS = dict[str, mag.types.ColorMatrix]


class ColorFiltersListSyncer(DataFileSyncer):
    JSON_DUMPER_KWARGS = dict(
        strip_properties=True,
        strip_privates=True,
        strip_nulls=True
    )
    YAML_DUMPER_KWARGS = dict(
        sort_keys=False,
    )

    def _dump(self, stream: TextIO):
        new_data = OrderedDict()
        for key, value in self.data.items():
            new_data[key] = tuple(
                line+' ' for line in mag.tools.matrix_to_str(value).split('\n')
            )
        self.data, new_data = new_data, self.data
        super()._dump(stream)
        self.data, new_data = new_data, self.data

    def _load(self, stream: TextIO):
        data = super()._load(stream)
        if data is not None:
            try:
                for key, value in data.items():
                    arr = ' '.join(value).split()
                    data[key] = tuple(
                        float(e) for e in arr
                    )
            except ValueError:
                return None
        return data


class ColorFiltersListController(Syncable):
    """
    List of color filters/effects used
    """

    def __init__(self):
        self.filters: COLOR_FILTERS = OrderedDict({
            'inversion': mag.const.COLOR_INVERSION_EFFECT,
            'grayscale': mag.const.COLOR_GRAYSCALE_EFFECT,
            'inverted grayscale': mag.const.COLOR_INVERTED_GRAYSCALE_EFFECT,
            'sepia': mag.const.COLOR_SEPIA_EFFECT,
            'tritanopia': mag.const.COLOR_BLIND_TRITANOPIA_EFFECT,
            'protanopia': mag.const.COLOR_BLIND_PROTANOPIA_EFFECT,
            'deuteranopia': mag.const.COLOR_BLIND_DEUTERANOPIA_EFFECT,
            'no effect': mag.const.COLOR_NO_EFFECT,
        })
        super().__init__(ColorFiltersListSyncer("color_filters", self.filters, OrderedDict[str, list[str]]))
        self._syncer.on_file_reloaded = lambda: self.load_filters(self._syncer.data)

    def setup(self):
        self._syncer.start()
        self._syncer.preserve_on_update()

    def load_filters(self, values: COLOR_FILTERS):
        self.filters = values
        self.on_filters_changed()

    def add_filter(self, name: str, rule: mag.types.ColorMatrix):
        self.filters[name] = rule
        self.on_filters_changed()
        self._syncer.save_file()

    def remove_filters(self, names: set[str]):
        if not names:
            return
        for name in names:
            del self.filters[name]
        self._syncer.save_file()
        self.on_filters_changed()

    def on_filters_changed(self):
        pass


class ColorFilter:
    close_manager = inject.attr(AppCloseManager)
    filters_holder = inject.attr(ColorFiltersListController)

    def __init__(self):
        self.test_mode = False
        self.api: mag.WinMagnificationAPI = None

    @execute_in_main_thread()
    def set_filter(
        self,
        color_filter: str,
        value: float,
        test=False,
    ):
        if self.test_mode and not test:
            return
        self.api.fullscreen.color_effect.make_transition(
            self.filters_holder.filters[color_filter],
            mag.const.COLOR_NO_EFFECT,
            value,
        )

    @execute_in_main_thread()
    def update_opacity(self, value: float):
        self.api.fullscreen.color_effect.transition_power = value

    def setup(self):
        self.api = mag.WinMagnificationAPI()
        self.close_manager.add_exit_handler(
            self.api.dispose
        )
