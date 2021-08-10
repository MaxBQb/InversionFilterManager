from typing import Generic, TypeVar
from dataclasses import dataclass
T = TypeVar('T')


@dataclass
class Rule(Generic[T]):
    blacklisted = None

    def check(self, info: T) -> bool:
        pass


class RulesController:
    RT = Rule

    def __init__(self):
        self.rules = dict()
        self.whitelist = dict()
        self.blacklist = dict()

    def load(self, rules: dict[str, RT]):
        self.rules = rules
        self.whitelist, self.blacklist = dict(), dict()
        for name, rule in rules.items():
            self.get_rules_section(rule.blacklisted)[name] = rule

    def add_rule(self, name: str, rule: Rule):
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

    def check(self, info: T):
        return (
            self.check_rules(info, self.whitelist) and
            not self.check_rules(info, self.blacklist)
        )

    def check_rules(self, info: T, rules: dict):
        return next(self.filter_rules(info, rules), None) is not None

    @staticmethod
    def filter_rules(info: T, rules: dict):
        return (name for name in rules
                if rules[name].check(info))

    def get_rules_section(self, blacklist: bool):
        if blacklist:
            return self.blacklist
        return self.whitelist
