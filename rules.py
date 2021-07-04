class Rule:
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

    def on_modified(self):
        pass
