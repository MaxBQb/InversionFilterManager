from rules import *
from dataclasses import dataclass
import re


@dataclass
class Text:
    raw: str = ""
    is_regex: bool = False

    @property
    def regex(self):
        if not self.is_regex:
            return None
        return re.compile(self.raw)


@dataclass
class AppRule(Rule):
    path: Text = Text()
    title: Text = None


class AppsRulesController(RulesController):
    rule_type = AppRule
