from typing import Generic, TypeVar
T = TypeVar('T')


class Rule(Generic[T]):
    def check(self, info: T) -> bool:
        pass


class RulesController:
    RT = Rule

    def __init__(self):
        self.rules = dict()

    def load(self, rules: dict[str, RT]):
        self.rules = rules

    def add_rule(self, name: str, rule: Rule):
        self.rules[name] = rule
        self.on_modified()

    def remove_rules(self, names: list[str]):
        if not names:
            return

        for name in names:
            del self.rules[name]
        self.on_modified()

    def on_modified(self):
        pass

    def check(self, info: T):
        return next(self.filter_rules(info), None) is not None

    def filter_rules(self, info: T):
        return (name for name in self.rules
                if self.rules[name].check(info))
