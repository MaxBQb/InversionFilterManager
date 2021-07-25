from PySimpleGUI import Frame, Button, Window, Text, Column
from utils import field_names_to_values


class PageSwitchController:
    class InnerID:
        PAGE_NUMBER: str
        PAGE_SET_FIRST: str
        PAGE_SET_LAST: str
        PAGE_NEXT: str
        PAGE_PREVIOUS: str

    def __init__(self, pages: list, key: str):
        self.pages = pages
        self.max_page = len(pages)
        self.last_page = self.max_page-1
        self.key = key
        self.keys = [
            self.get_specific_key(str(i))
            for i in range(self.max_page)
        ]
        self.current_page = 0
        self.selected = self.keys[self.current_page]

        self.id = field_names_to_values(
            self.get_specific_key("{}")
        )(self.InnerID)()

        self.controls_sym = {
            self.id.PAGE_SET_FIRST: ('<<', (0, False)),
            self.id.PAGE_PREVIOUS: ('<', (-1, True)),
            self.id.PAGE_NEXT: ('>', (1, True)),
            self.id.PAGE_SET_LAST: ('>>', (self.last_page, False)),
        }

    def get_page_holder(self, common_options={}):
        return Column([[
            Frame(**(self.get_page_options(i)
                     | common_options))
            for i in range(self.max_page)
        ]], pad=(0, 0))

    def get_controls(self, common_options={}):
        if self.max_page == 1:
            return []
        shown = [k for k, v in self._get_controls_visibility() if v]
        controls: list = [
            Column([[
                Button(**(dict(
                    button_text=symbol,
                    key=control_key,
                    visible=control_key in shown
                ) | common_options))
            ]], pad=(0, 0))
            for control_key, (symbol, (_, relative)) in self.controls_sym.items()
        ]
        controls.insert(2, Column([[
                Text(self.get_page_text(),
                     key=self.id.PAGE_NUMBER)
            ]], pad=(12, 0))
        )
        return controls

    def get_page_options(self, page: int) -> dict:
        return dict(
            title='',
            layout=self.pages[page],
            key=self.keys[page],
            border_width=0,
            visible=self.is_selected(page)
        )

    def get_specific_key(self, key: str) -> str:
        return self.key + key + "-"

    def is_selected(self, page: int):
        return self.current_page == page

    def select_page(self, new_pos: int, relative: bool = False):
        if relative:
            new_pos = self.get_next_pos(
                self.current_page, self.max_page, new_pos
            )
        self.current_page = new_pos
        self.selected = self.keys[new_pos]

    @staticmethod
    def get_next_pos(pos: int, length: int, step=1):
        new_pos = (pos + step) % length
        if new_pos < 0:
            new_pos += length
        return new_pos

    def handle_event(self, event, window: Window):
        new_page_args = self.controls_sym.get(event)
        if new_page_args is None:
            return False
        window[self.selected].update(visible=False)
        self.select_page(*new_page_args[1])
        window[self.selected].update(visible=True)
        window[self.id.PAGE_NUMBER].update(
            self.get_page_text()
        )
        for key, disable in self._get_controls_visibility():
            window[key].update(visible=disable)
        return True

    def get_page_text(self):
        max_page = str(self.max_page)
        current_page = str(self.current_page + 1)
        current_page = current_page.zfill(len(max_page))
        return current_page + " / " + max_page

    def _get_controls_visibility(self):
        is_first_page = self.current_page != 0
        is_last_page = self.current_page != self.last_page
        need_relative_controls = self.max_page > 2
        return (
            (self.id.PAGE_PREVIOUS, is_first_page and need_relative_controls),
            (self.id.PAGE_SET_FIRST, is_first_page),
            (self.id.PAGE_NEXT, is_last_page and need_relative_controls),
            (self.id.PAGE_SET_LAST, is_last_page)
        )

    @classmethod
    def from_list(cls, elements: list, columns: int = 6, rows: int = 10):
        from functools import partial
        return partial(cls, pages=cls.array_split(
            cls.array_split(elements, columns), rows
        ))

    @staticmethod
    def array_split(arr: list, max_len: int):
        return [arr[i:i + max_len]
                for i in range(0, len(arr), max_len)]
