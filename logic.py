import pyautogui as gui
from winregal import RegKey
from configobj import ConfigObj


class App:
    def __init__(self):
        gui.FAILSAFE = False
        self.state_controller = FilterStateController(self)
        self.config = ConfigManager("config").get_config()

    def run(self):
        from active_window_checker import listen_switch_events
        listen_switch_events(self.state_controller.on_active_window_switched)


class AppElement:
    def __init__(self, app: App):
        self.app = app


class InversionFilterController:
    @staticmethod
    def is_active():
        with RegKey(r"HKEY_CURRENT_USER\Software\Microsoft\ColorFiltering") as key:
            return bool(key.get_value("Active").data)

    @staticmethod
    def set(value):
        if value != InversionFilterController.is_active():
            InversionFilterController.toggle()

    @staticmethod
    def toggle():
        gui.hotkey("ctrl", "win", "c")


class FilterStateController(AppElement):
    def on_active_window_switched(self,
                                  hWinEventHook,
                                  event,
                                  hwnd,
                                  idObject,
                                  idChild,
                                  dwEventThread,
                                  dwmsEventTime):
        from active_window_checker import get_window_info, eventTypes, getActiveWindow
        hwnd = getActiveWindow()
        title, processID, shortName, alt_hwnd = get_window_info(hwnd, idObject, dwEventThread)
        if self.app.config["display"]["show_events"]:
            print(shortName, eventTypes.get(event, hex(event)))
        InversionFilterController.set(shortName == "System32\mspaint.exe")


class ConfigManager:
    def __init__(self, name: str):
        self.name = name

    def get_config(self):
        config = ConfigObj(infile=self.name + ".ini",
                           configspec=self.name + "_description.ini",
                           create_empty=True,
                           write_empty_values=True)
        self.validate_config(config)
        return config

    def validate_config(self, config: ConfigObj):
        from validate import Validator
        test = config.validate(Validator(), copy=True)
        if not test:
            config.restore_defaults()
            config.validate(Validator(), copy=True)
            print("Invalid configuration found.")
            print(f"Restore defaults for '{config.filename}'")
        config.initial_comment = ["Feel free to edit this config file"]
        config.write()
