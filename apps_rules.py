from re import compile
from rules import *
from dataclasses import dataclass
from active_window_checker import WindowInfo


@dataclass
class AppRule(Rule):
    path: str = None
    path_regex: str = None
    title: str = None
    title_regex: str = None
    use_root_title: bool = None

    def __post_init__(self):
        if self.path is not None:
            self.path_regex = None
        elif self.path_regex is None:
            raise RuntimeError("Unable to create rule with no path condition")

        self._check_title = True
        if self.title is not None:
            self.title_regex = None
        elif self.title_regex is None:
            self._check_title = False

        self._title_regex = try_compile(self.title_regex)
        self._path_regex = try_compile(self.path_regex)

    def check(self, info: WindowInfo) -> bool:
        return self.check_path(info) and self.check_title(info)

    def check_path(self, info: WindowInfo):
        return check_text(info.path, self.path, self._path_regex)

    def check_title(self, info: WindowInfo):
        if not self._check_title:
            return True
        title = info.root_title if self.use_root_title else info.title
        return check_text(title, self.title, self._title_regex)


class AppsRulesController(RulesController):
    RT = AppRule


def try_compile(raw_regex: str):
    if not raw_regex:
        return
    return compile(raw_regex)


def check_text(text, plain, regex):
    if regex:
        return regex.fullmatch(text) is not None
    return text == plain
