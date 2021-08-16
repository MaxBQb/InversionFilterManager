"""Log window focus and appearance.
Written to try to debug some window popping up and stealing focus from my
Spelunky game for a split second.
Developed with 32-bit python on Windows 7. Might work in other environments,
but some of these APIs might not exist before Vista.
Much credit to Eric Blade for this:
https://mail.python.org/pipermail/python-win32/2009-July/009381.html
and David Heffernan:
        http://stackoverflow.com/a/15898768/9585
"""

# using pywin32 for constants and ctypes for everything else seems a little
# indecisive, but whatevs.
import win32api
import win32con
import win32gui
import win32process
from functools import cached_property
from dataclasses import dataclass
import sys
import ctypes
import ctypes.wintypes

user32 = ctypes.windll.user32
ole32 = ctypes.windll.ole32
kernel32 = ctypes.windll.kernel32

WinEventProcType = ctypes.WINFUNCTYPE(
    None,
    ctypes.wintypes.HANDLE,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.HWND,
    ctypes.wintypes.LONG,
    ctypes.wintypes.LONG,
    ctypes.wintypes.DWORD,
    ctypes.wintypes.DWORD
)


# The types of events we want to listen for, and the names we'll use for
# them in the log output. Pick from
# http://msdn.microsoft.com/en-us/library/windows/desktop/dd318066(v=vs.85).aspx
eventTypes = {
    win32con.EVENT_SYSTEM_FOREGROUND: "Foreground",
    win32con.EVENT_OBJECT_FOCUS: "Focus",
    #win32con.EVENT_OBJECT_SHOW: "Show",
    win32con.EVENT_SYSTEM_DIALOGSTART: "Dialog",
    win32con.EVENT_SYSTEM_CAPTURESTART: "Capture",
    win32con.EVENT_SYSTEM_MINIMIZEEND: "UnMinimize"
}

# limited information would be sufficient, but our platform doesn't have it.
processFlag = getattr(win32con, 'PROCESS_QUERY_LIMITED_INFORMATION',
                      win32con.PROCESS_QUERY_INFORMATION)

threadFlag = getattr(win32con, 'THREAD_QUERY_LIMITED_INFORMATION',
                     win32con.THREAD_QUERY_INFORMATION)


@dataclass
class WindowInfo:
    hwnd: int
    title: str = ""
    path: str = ""
    pid: int = None
    root_title: str = ""

    @property
    def name(self) -> str:
        return self.path.split('\\')[-1]

    @cached_property
    def titles(self):
        return {*filter(
            None, titles(parents(self.hwnd))
        ), self.root_title}


def getProcessFilename(processID):
    hProcess = kernel32.OpenProcess(processFlag, 0, processID)
    if not hProcess:
        raise ProcessLookupError(f"OpenProcess({processID}) failed: {ctypes.WinError()}")

    try:
        filenameBufferSize = ctypes.wintypes.DWORD(4096)
        filename = ctypes.create_unicode_buffer(filenameBufferSize.value)
        kernel32.QueryFullProcessImageNameW(hProcess, 0, ctypes.byref(filename),
                                            ctypes.byref(filenameBufferSize))

        return filename.value
    finally:
        kernel32.CloseHandle(hProcess)


def get_window_info(hwnd) -> WindowInfo:
    try:
        winfo = WindowInfo(
            hwnd,
            win32gui.GetWindowText(hwnd),
            pid=win32process.GetWindowThreadProcessId(hwnd)[1]
        )
        if winfo.pid:
            winfo.path = getProcessFilename(winfo.pid)

    except ProcessLookupError:
        return None

    root_hwnd = get_root(hwnd)
    if root_hwnd != 0:
        winfo.root_title = win32gui.GetWindowText(root_hwnd)
        if not winfo.title:
            winfo.title = winfo.root_title
    return winfo


def is_root(hwnd: int, candidate_hwnd: int):
    return (candidate_hwnd != 0
            and (hwnd == candidate_hwnd
                 or win32gui.IsChild(candidate_hwnd, hwnd)))


def get_root(hwnd: int):
    active = (win32gui.GetForegroundWindow() or
              win32gui.GetFocus())

    if is_root(hwnd, active):
        return active

    try:
        owner = win32gui.GetWindow(hwnd, win32con.GW_OWNER)
        if is_root(hwnd, owner):
            return owner
    except win32gui.error:
        pass

    start = hwnd
    last_hwnd = 0
    for last_hwnd in parents(hwnd):
        pass
    return last_hwnd if start != last_hwnd else 0


def setHook(WinEventProc, eventType):
    return user32.SetWinEventHook(
        eventType,
        eventType,
        0,
        WinEventProc,
        0,
        0,
        win32con.WINEVENT_OUTOFCONTEXT
    )


def parents(hwnd):
    if not hwnd:
        return
    try:
        while True:
            hwnd = win32gui.GetParent(hwnd)
            if not hwnd:
                break
            yield hwnd
    except win32gui.error:
        pass


def titles(iterable):
    for hwnd in iterable:
        yield win32gui.GetWindowText(hwnd)


def listen_switch_events(callback, out_thread_id):
    ole32.CoInitialize(0)

    WinEventProc = WinEventProcType(callback)
    user32.SetWinEventHook.restype = ctypes.wintypes.HANDLE

    hookIDs = [setHook(WinEventProc, et) for et in eventTypes.keys()]
    if not any(hookIDs):
        print('SetWinEventHook failed')
        sys.exit(1)

    out_thread_id[0] = win32api.GetCurrentThreadId()
    win32gui.PumpMessages()

    for hookID in hookIDs:
        user32.UnhookWinEvent(hookID)
    ole32.CoUninitialize()
