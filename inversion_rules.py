from re import compile
from dataclasses import dataclass
from active_window_checker import WindowInfo


@dataclass
class InversionRule:
    """
    Specifies if current window requires to
    toggle inversion color filter

    'requirements' defines by user
    """

    path: str = None
    path_regex: str = None
    title: str = None
    title_regex: str = None
    use_root_title: bool = None
    blacklisted = None

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


class InversionRulesController:
    def __init__(self):
        self.rules = dict()
        self.whitelist = dict()
        self.blacklist = dict()

    def load(self, rules: dict[str, InversionRule]):
        self.rules = rules
        self.whitelist, self.blacklist = dict(), dict()
        for name, rule in rules.items():
            self.get_rules_section(rule.blacklisted)[name] = rule

    def add_rule(self, name: str, rule: InversionRule):
        self.rules[name] = rule
        self.get_rules_section(rule.blacklisted)[name] = rule
        self.on_modified()

    def remove_rules(self, names: set[str]):
        if not names:
            return

        for name in names:
            del self.get_rules_section(
                self.rules[name].blacklisted
            )[name]
            del self.rules[name]
        self.on_modified()

    def on_modified(self):
        pass

    def check(self, info: WindowInfo):
        return (
            self.check_rules(info, self.whitelist) and
            not self.check_rules(info, self.blacklist)
        )

    def check_rules(self, info: WindowInfo, rules: dict):
        return next(self.filter_rules(info, rules), None) is not None

    @staticmethod
    def filter_rules(info: WindowInfo, rules: dict):
        return (name for name in rules
                if rules[name].check(info))

    def get_rules_section(self, blacklist: bool):
        if blacklist:
            return self.blacklist
        return self.whitelist


def try_compile(raw_regex: str):
    if not raw_regex:
        return
    return compile(raw_regex)


def check_text(text, plain, regex):
    if regex:
        return regex.fullmatch(text) is not None
    return text == plain
