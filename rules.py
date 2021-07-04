class Rule:
    def check(self, info) -> bool:
        pass


class RulesController:
    rule_type = Rule

    def __init__(self):
        self.rules = dict()

    def load(self, rules):
        self.rules = rules

    def add_rule(self, name: str, rule: Rule):
        self.rules[name] = rule
        self.on_modified()

    def remove_rules(self, names):
        if not names:
            return

        for name in names:
            del self.rules[name]
        self.on_modified()

    def on_modified(self):
        pass

    def check(self, info):
        return next(self.filter_rules(info), None) is not None

    def filter_rules(self, info):
        return (name for name in self.rules
                if self.rules[name].check(info))
