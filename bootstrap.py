import ctypes
import sys
from typing import Optional

shell = ctypes.windll.shell32

ERRORS = {
    0: 'The operating system is out of memory or resources.',
    2: 'The specified file was not found.',
    3: 'The specified path was not found.',
    5: 'The operating system denied access '
       'to the specified file.',
    8: 'There was not enough memory to complete the operation.',
    11: 'The .exe file is invalid '
        '(non-Win32 .exe or error in .exe image).',
    26: 'A sharing violation occurred.',
    27: 'The file name association '
        'is incomplete or invalid.',
    28: 'The DDE transaction could not '
        'be completed because the request timed out.',
    29: 'The DDE transaction failed.',
    30: 'The DDE transaction could not be completed '
        'because other DDE transactions were being processed.',
    31: 'There is no application associated '
        'with the given file name extension.',
    32: 'The specified DLL was not found.',
}


def request_admin_rights() -> bool:
    # msdn.microsoft.com/en-us/library/windows/desktop/bb762153(v=vs.85).aspx
    if shell.IsUserAnAdmin():
        return False
    hinstance = shell.ShellExecuteW(
        None, 'runas', sys.executable, sys.argv[0], None, 1
    )
    if hinstance <= 32:
        raise RuntimeError(ERRORS.get(hinstance, f"{hinstance}: Unknown error"))
    return True


def try_request_admin_rights() -> Optional[bool]:
    try:
        return request_admin_rights()
    except RuntimeError as error:
        print(error.args[0], file=sys.stderr)
