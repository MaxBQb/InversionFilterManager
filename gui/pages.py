from PySimpleGUI import Frame, Button, Window, Text, Column
from utils import field_names_to_values, cycled_shift


class PageSwitchController:
    class InnerID:
        PAGE_NUMBER: str
        PAGE_SET_FIRST: str
        PAGE_SET_LAST: str
        PAGE_NEXT: str
        PAGE_PREVIOUS: str

    def __init__(self,
                 pages: list,
                 key: str,
                 page_format: str = None):
        self.pages = pages
        self.max_page = len(pages)
        self.last_page = self.max_page - 1
        self.key = key
        self.keys = [
            self.get_specific_key(str(i))
            for i in range(self.max_page)
        ]
        self.current_page = 0
        self.selected = self.keys[self.current_page]
        self.page_format = page_format or "{} / {}"
        self._max_pages_text_len = len(self.page_format.format(
            *(self.max_page,) * 2
        )) + 2

        self.id = field_names_to_values(
            self.get_specific_key("{}")
        )(self.InnerID)()

        self._controls_sym = {
            self.id.PAGE_SET_FIRST: ('<<', 0),
            self.id.PAGE_PREVIOUS: ('<', -1),
            self.id.PAGE_NEXT: ('>', 1),
            self.id.PAGE_SET_LAST: ('>>', self.last_page),
        }

    def get_pages_holder(self, common_options={}):
        return Column([[
            Frame(**(self.get_page_options(i)
                     | common_options))
            for i in range(self.max_page)
        ]], pad=(0, 0))

    def get_controls(self, common_options={}):
        if self.max_page == 1:
            return []
        disabled = {k for k, v in self._get_controls_disabled_states() if v}
        controls: list = [
            Column([[
                Button(**(dict(
                    button_text=symbol,
                    key=control_key,
                    disabled=control_key in disabled
                ) | common_options))
            ]], pad=(0, 0))
            for control_key, (symbol, _) in self._controls_sym.items()
        ]
        controls.insert(len(controls) // 2, Column([[
            Text(self.get_page_text(),
                 font=("Consolas", 10),
                 key=self.id.PAGE_NUMBER)
        ]], pad=(12, 0)))
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

    def select_page(self, new_pos: int):
        if new_pos not in (0, self.last_page):
            new_pos = cycled_shift(
                self.current_page,
                self.max_page,
                new_pos
            )
        self.current_page = new_pos
        self.selected = self.keys[new_pos]

    def handle_event(self, event, window: Window):
        new_page_args = self._controls_sym.get(event)
        if new_page_args is None:
            return False
        window[self.selected].update(visible=False)
        self.select_page(new_page_args[1])
        window[self.selected].update(visible=True)
        window[self.id.PAGE_NUMBER].update(
            self.get_page_text()
        )
        for key, disable in self._get_controls_disabled_states():
            window[key].update(disabled=disable)
        return True

    def get_page_text(self):
        return self.page_format.format(
            self.current_page + 1,
            self.max_page
        ).center(self._max_pages_text_len)

    def _get_controls_disabled_states(self):
        is_first_page = self.current_page == 0
        is_last_page = self.current_page == self.last_page
        return (
            (name, is_first_page if value < 1 else is_last_page)
            for name, (_, value) in self._controls_sym.items()
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
