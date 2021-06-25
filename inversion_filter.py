import pyautogui as gui


class InversionFilterController:
    def toggle(self):
        gui.hotkey("ctrl", "win", "c")

inversion_filter = InversionFilterController()