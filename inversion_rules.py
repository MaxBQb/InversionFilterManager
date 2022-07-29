import typing
from dataclasses import dataclass
from enum import Enum, auto
from re import compile
from typing import TYPE_CHECKING, TextIO

from commented_config import CommentsHolder, get_comments_holder
from file_tracker import DataFileSyncer, Syncable

if TYPE_CHECKING:
    from active_window_checker import WindowInfo


class LookForTitle(Enum):
    ANY = auto()
    CURRENT = auto()
    ROOT = auto()


class RuleType(Enum):
    INCLUDE = auto()
    EXCLUDE = auto()
    IGNORE = auto()


@dataclass
class InversionRule:
    """
    Filter specific window/app
    If information given matches with filters
    then rule is active
    """
    _comments_ = CommentsHolder()
    __comment_base = "{{name}}: {{typename}}" \
                     "{}Example: {{name}}: {}"

    path: str = None
    _comments_.add(__comment_base.format("""
        Match plain path text
        Conflict with path_regex
    """, "C:\Windows\explorer.exe"), locals())

    path_regex: str = None
    _comments_.add(__comment_base.format("""
        Match path with regular expression
        Conflict with path
    """, "C:\\Program\ Files\\Microsoft\ Office\\root\\Office\d+\\WINWORD\.EXE"), locals())

    title: str = None
    _comments_.add(__comment_base.format("""
        Match plain title text
        Conflict with title_regex
    """, "TeamViewer options"), locals())

    title_regex: str = None
    _comments_.add(__comment_base.format("""
        Match title with regular expression
        Conflict with title
    """, ".?Ramus.*"), locals())

    look_for_title: LookForTitle = None
    _comments_.add(__comment_base.format(f"""
        Source of title: {' | '.join(e.name for e in LookForTitle)}
        \t{LookForTitle.ANY.name} - windows from root to current
        \t{LookForTitle.ROOT.name} - Main window
        \t{LookForTitle.CURRENT.name} - Current window (or text element)
    """, LookForTitle.ANY.name), locals())

    type: RuleType = None
    _comments_.add(__comment_base.format(f"""
         Type of rule: {' | '.join(e.name for e in RuleType)}
        \t{RuleType.INCLUDE.name} - if this rule is active, then inversion needed
        \t{RuleType.EXCLUDE.name} - if this rule is active, then no inversion needed
        \t{RuleType.IGNORE.name} - if this rule is active, then do nothing
    """, RuleType.INCLUDE.name), locals())

    remember_processes: bool = None
    _comments_.add(__comment_base.format("""
        Once this rule is active, 
        pid of target app will always activate rule,
    """, "false"), locals())

    color_filter: str = None
    _comments_.add(__comment_base.format("""
        Filter name (id from filters list file)
    """, "inversion"), locals())

    color_filter_opacity: float = None
    _comments_.add(__comment_base.format("""
        How transparent looks filter applied:
        \t0.0 - No color filter applied
        \t1.0 - Color filter applied with full power
        \t0.0 < x < 1.0 - Color filter applied blended with current color
        Values around 0.5 are not recommended
    """, "1.0"), locals())

    def __post_init__(self):
        if self.color_filter == 'inversion':
            self.color_filter = None
        if self.color_filter_opacity == 1.0:
            self.color_filter_opacity = None

        if self.remember_processes:
            self._pids = set()
        else:
            self.remember_processes = None

        self._type = self.type or RuleType.INCLUDE
        if self.type == RuleType.INCLUDE:
            self.type = None

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

    def get_type(self):
        return self._type

    def is_active(self, info: 'WindowInfo') -> bool:
        active = (self.check_path(info)
                  and self.check_title(info))

        if not self.remember_processes:
            return active

        if active:
            self._pids.add(info.pid)

        return info.pid in self._pids

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
    if there are some ignored active rules
    Recommends to do nothing
    """

    def __init__(self):
        self.rules: RULES = dict()
        self.included: RULES = dict()
        self.excluded: RULES = dict()
        self.ignored: RULES = dict()
        super().__init__(RulesSyncer("inversion_rules", self.rules, RULES))
        self._syncer.on_file_reloaded = lambda: self.load_rules(self._syncer.data)

    def setup(self):
        self._syncer.start()
        self._syncer.preserve_on_update()

    def load_rules(self, rules: RULES):
        self.rules = rules
        self.included, self.excluded, self.ignored = dict(), dict(), dict()
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

    def get_filter(self, info: 'WindowInfo') -> typing.Optional[tuple[str, float]]:
        possibilities = (
            (self.ignored, None),
            (self.excluded, False),
            (self.included, True),
        )
        for rules, result in possibilities:
            rule_name = next(self.get_active_rules(info, rules), None)
            if rule_name is None:
                continue
            rule: InversionRule = rules[rule_name]
            if result:
                color_filter = rule.color_filter
                opacity = rule.color_filter_opacity
                if color_filter is None:
                    color_filter = 'inversion'
                if opacity is None:
                    opacity = 1.0
                return color_filter, opacity
            return 'no effect', 1.0
        return 'no effect', 1.0

    def has_active_rules(self, info: 'WindowInfo', rules: RULES = None):
        if rules is None:
            rules = self.rules
        return next(self.get_active_rules(info, rules), None) is not None

    @staticmethod
    def get_active_rules(info: 'WindowInfo', rules: RULES):
        return (name for name in rules
                if rules[name].is_active(info))

    def _detect_accessory(self, rule: InversionRule):
        return {
            RuleType.INCLUDE: self.included,
            RuleType.EXCLUDE: self.excluded,
            RuleType.IGNORE: self.ignored,
        }.get(rule.get_type())

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

    def _dump(self, stream: TextIO):
        for comments in get_comments_holder(InversionRule).content.values():
            stream.writelines([*comments, "\n"])

        if self.data:
            super()._dump(stream)
