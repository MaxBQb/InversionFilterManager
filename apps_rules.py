from rules import *
from dataclasses import dataclass
from active_window_checker import WindowInfo
import re


@dataclass
class Text(Rule):
    raw: str = ""
    is_regex: bool = False

    def __post_init__(self):
        if self.is_regex:
            self._regex = re.compile(self.raw)
        else:
            self.is_regex = None

    def check(self, info: str) -> bool:
        return (self._regex.fullmatch(info) is not None) \
                if self.is_regex \
                else info == self.raw


@dataclass
class AppRule(Rule):
    path: Text = Text()
    title: Text = None

    def check(self, info: WindowInfo) -> bool:
        if not self.path.check(info.path):
            return False

        if self.title is None:
            return True

        return self.title.check(info.title)


class AppsRulesController(RulesController):
    RT = AppRule
