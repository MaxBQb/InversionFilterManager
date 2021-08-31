from dataclasses import dataclass
from enum import Enum, auto
from re import compile
from typing import TYPE_CHECKING
from file_tracker import DataFileSyncer, Syncable

if TYPE_CHECKING:
    from active_window_checker import WindowInfo


class LookForTitle(Enum):
    ANY = auto()
    CURRENT = auto()
    ROOT = auto()


@dataclass
class InversionRule:
    """
    Filter specific window/app
    If information given matches with filters
    then rule is active
    """

    path: str = None
    path_regex: str = None
    title: str = None
    title_regex: str = None
    look_for_title: LookForTitle = None
    exclude: bool = None

    def __post_init__(self):
        self.exclude = self.exclude or None

        if self.path is not None:
            self.path_regex = None
        elif self.path_regex is None:
            raise RuntimeError("Unable to create rule with no path condition")

        self._check_title = True
        if self.title is not None:
            self.title_regex = None
        elif self.title_regex is None:
            self._check_title = False
            self.look_for_title = None

        self._title_regex = try_compile(self.title_regex)
        self._path_regex = try_compile(self.path_regex)

    def is_active(self, info: 'WindowInfo') -> bool:
        return self.check_path(info) and self.check_title(info)

    def check_path(self, info: 'WindowInfo'):
        return check_text(info.path, self.path, self._path_regex)

    def check_title(self, info: 'WindowInfo'):
        if not self._check_title:
            return True
        if self.look_for_title == LookForTitle.ANY:
            if self.title:
                return self.title in info.titles

            return any(
                self._title_regex.fullmatch(title)
                for title in info.titles
            )

        title = (info.root_title
                 if self.look_for_title == LookForTitle.ROOT
                 else info.title)
        return check_text(title, self.title, self._title_regex)


RULES = dict[str, InversionRule]


class InversionRulesController(Syncable):
    """
    Determines when to use inversion color filter
    Accumulates active rules
    if no active rules found or
    if there are some excluded active rules
    Recommends to turn filter off, otherwise: on
    """

    def __init__(self):
        self.rules: RULES = dict()
        self.included: RULES = dict()
        self.excluded: RULES = dict()
        super().__init__(RulesSyncer("inversion_rules", self.rules, RULES))
        self._syncer.on_file_reloaded = lambda: self.load_rules(self._syncer.data)

    def setup(self):
        self._syncer.start()
        self._syncer.preserve_on_update()

    def load_rules(self, rules: RULES):
        self.rules = rules
        self.included, self.excluded = dict(), dict()
        for name, rule in rules.items():
            self._detect_accessory(rule)[name] = rule
        self.on_rules_changed()

    def add_rule(self, name: str, rule: InversionRule):
        self.rules[name] = rule
        self._detect_accessory(rule)[name] = rule
        self.on_rules_changed()
        self._syncer.save_file()

    def remove_rules(self, names: set[str]):
        if not names:
            return

        for name in names:
            del self._detect_accessory(self.rules[name])[name]
            del self.rules[name]
        self._syncer.save_file()
        self.on_rules_changed()

    def is_inversion_required(self, info: 'WindowInfo'):
        return (
            self.has_active_rules(info, self.included) and
            not self.has_active_rules(info, self.excluded)
        )

    def has_active_rules(self, info: 'WindowInfo', rules: RULES = None):
        if rules is None:
            rules = self.rules
        return next(self.get_active_rules(info, rules), None) is not None

    @staticmethod
    def get_active_rules(info: 'WindowInfo', rules: RULES):
        return (name for name in rules
                if rules[name].is_active(info))

    def _detect_accessory(self, rule: InversionRule):
        if rule.exclude:
            return self.excluded
        return self.included

    def on_rules_changed(self):
        pass


def try_compile(raw_regex: str):
    if not raw_regex:
        return
    return compile(raw_regex)


def check_text(text: str, plain: str, regex):
    if regex:
        return bool(regex.fullmatch(text))
    return text == plain


class RulesSyncer(DataFileSyncer):
    JSON_DUMPER_KWARGS = dict(
        strip_properties=True,
        strip_privates=True,
        strip_nulls=True
    )

    def _dump(self, stream):
        if not self.data:
            stream.truncate(0)
        else:
            super()._dump(stream)
