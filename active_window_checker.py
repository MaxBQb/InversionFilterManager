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
import win32con
import win32gui
import win32process
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


def getProcessFilename(processID):
    hProcess = kernel32.OpenProcess(processFlag, 0, processID)
    if not hProcess:
        print(f"OpenProcess({processID}) failed: {ctypes.WinError()}", file=sys.stderr)
        return None

    try:
        filenameBufferSize = ctypes.wintypes.DWORD(4096)
        filename = ctypes.create_unicode_buffer(filenameBufferSize.value)
        kernel32.QueryFullProcessImageNameW(hProcess, 0, ctypes.byref(filename),
                                            ctypes.byref(filenameBufferSize))

        return filename.value
    finally:
        kernel32.CloseHandle(hProcess)


def get_window_info(hwnd) -> WindowInfo:
    winfo = WindowInfo(
        hwnd,
        win32gui.GetWindowText(hwnd),
        pid=win32process.GetWindowThreadProcessId(hwnd)[1]
    )

    if winfo.pid:
        winfo.path = getProcessFilename(winfo.pid)

    root_hwnd = get_root(hwnd)
    if root_hwnd != 0:
        winfo.root_title = win32gui.GetWindowText(root_hwnd)
        if not winfo.title:
            winfo.title = winfo.root_title
    return winfo


def get_root(hwnd: int):
    active = (win32gui.GetForegroundWindow() or
              win32gui.GetFocus())

    if active and (hwnd == active or
                   win32gui.IsChild(active, hwnd)):
        return active

    start = hwnd
    last_hwnd = 0
    try:
        while hwnd != 0:
            last_hwnd = hwnd
            hwnd = win32gui.GetParent(hwnd)
    except win32gui.error:
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


async def listen_switch_events(callback):
    ole32.CoInitialize(0)

    WinEventProc = WinEventProcType(callback)
    user32.SetWinEventHook.restype = ctypes.wintypes.HANDLE

    hookIDs = [setHook(WinEventProc, et) for et in eventTypes.keys()]
    if not any(hookIDs):
        print('SetWinEventHook failed')
        sys.exit(1)

    msg = ctypes.wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
        user32.TranslateMessage(msg)
        user32.DispatchMessageW(msg)

    for hookID in hookIDs:
        user32.UnhookWinEvent(hookID)
    ole32.CoUninitialize()
