import pyautogui as gui
from winregal import RegKey


class App:
    def __init__(self):
        gui.FAILSAFE = False
        self.state_controller = FilterStateController(self)

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
        print(shortName, eventTypes.get(event, hex(event)))
        InversionFilterController.set(shortName == "System32\mspaint.exe")
