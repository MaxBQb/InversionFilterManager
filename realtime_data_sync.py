from file_tracker import FileTracker
from configobj import ConfigObj
from rules import RulesController
import jsons
import yaml


class ConfigFileManager(FileTracker):
    def __init__(self, name: str):
        self.config = ConfigObj(infile=name + ".ini",
                                configspec=name + "_description.ini",
                                create_empty=True,
                                write_empty_values=True)
        super().__init__(self.config.filename)

    def load_file(self):
        self.validate_config()

    def reload_file(self):
        self.config.reload()
        print(("Changes for '{}' applied"
               if self.validate_config() else
               "Changes for '{}' fixed & applied").format(self.config.filename))

    def validate_config(self):
        from validate import Validator
        validator = Validator()
        test = self.config.validate(validator,
                                    copy=True,
                                    preserve_errors=True)
        check_failed = test is not True
        if test is False:
            print("Invalid configuration found.")
            self.on_fully_invalid(Validator())
            print(f"Restore defaults for '{self.config.filename}'")
        elif check_failed:
            print("Invalid configuration parts found.")
            self.on_partially_invalid(test)
            print(f"Restore defaults for this parts of '{self.config.filename}'")
        self.config.initial_comment = ["Feel free to edit this config file"]
        with self.observer.overlook():
            self.config.write()
        return not check_failed

    def on_fully_invalid(self, validator):
        self.config.restore_defaults()
        self.config.validate(validator, copy=True)  # restore defaults as real values

    def on_partially_invalid(self, validation_response: dict):
        from configobj import flatten_errors
        for sections, key, error in flatten_errors(self.config, validation_response):
            if not error:
                error = "missing"
            pointer = self.config
            for section in sections:
                pointer = pointer[section]
            print('.'.join(sections + [key]) + ":", error)
            pointer.restore_default(key)
            pointer[key] = pointer[key]  # current = default


class RulesFileManager(FileTracker):
    def __init__(self, name: str, rules_controller: RulesController):
        self.rules = None
        self.rules_controller = rules_controller
        self.rules_controller.on_modified = self.save_rules
        super().__init__(name + "_rules.yaml")

    def load_file(self):
        try:
            with self.observer.overlook():
                with open(self.filename) as f:
                    self.rules = yaml.safe_load(f)
            if self.rules is None:
                self.rules = {}
            for key in self.rules:
                self.rules[key] = jsons.load(self.rules[key],
                                             self.rules_controller.rule_type)
        except FileNotFoundError:
            self.rules = {}
        finally:
            self.dump_file()

    def save_rules(self):
        self.rules = self.rules_controller.rules
        self.dump_file()

    def dump_file(self):
        with self.observer.overlook():
            with open(self.filename, "w") as f:
                if self.rules:
                    yaml.dump(jsons.dump(self.rules,
                                         strip_properties=True,
                                         strip_privates=True,
                                         strip_nulls=True), f)

    def on_file_loaded(self):
        self.rules_controller.load(self.rules)

    def on_file_reloaded(self):
        print(f"Changes for '{self.filename}' applied")
