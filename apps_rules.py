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
            self.check = self.check_regex
        else:
            self.check = self.check_text
            self.is_regex = None

    @property
    def regex(self):
        if not self.is_regex:
            return None
        return re.compile(self.raw)

    def check_text(self, info: str) -> bool:
        return info == self.raw

    def check_regex(self, info: str) -> bool:
        return self.regex.fullmatch(info) is not None


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
    rule_type = AppRule
