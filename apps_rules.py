from rules import *
from dataclasses import dataclass
from active_window_checker import WindowInfo
from text_matcher import get_matcher


@dataclass
class AppRule(Rule):
    path: str = None
    path_regex: str = None
    title: str = None
    title_regex: str = None

    _regex_suffix = '_regex'

    def __post_init__(self):
        self._define_text_matchers()

    def with_options(self,
                     path: tuple[str, bool],
                     title: tuple[str, bool]):
        text_matcher_fields = (
            ('path', path),
            ('title', title),
        )
        for field, value in text_matcher_fields:
            self._set_text_matcher(field, get_matcher(*value))
            self._set_text_matcher_raw(field, *value)

    def check(self, info: WindowInfo) -> bool:
        if not self._is_path_match(info.path):
            return False
        return self._is_title_match(info.title)

    def _define_text_matchers(self):
        text_matcher_fields = [(field.removesuffix(self._regex_suffix), field)
                               for field in vars(self)
                               if field.endswith(self._regex_suffix)]
        for field, field_regex in text_matcher_fields:
            value_regex = getattr(self, field_regex)
            self._set_text_matcher(field, get_matcher(
               getattr(self, field) or value_regex,
               value_regex is not None
            ))

    def _set_text_matcher_raw(self, field: str, value: str, is_regex: bool):
        if is_regex:
            field += self._regex_suffix
        setattr(self, field, value)

    def _set_text_matcher(self, field: str, matcher):
        setattr(self, f'_is_{field}_match', matcher)


class AppsRulesController(RulesController):
    RT = AppRule
