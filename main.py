import argparse
from asyncio import run

import inject
import win32api
import win32con
import win32event
from winerror import ERROR_ALREADY_EXISTS

from app_start import AppStartManager


def lock_instance(allow_multiple=False):
    from _meta import __instance_lock_key__
    mutex = win32event.CreateMutex(None, False, __instance_lock_key__)
    if win32api.GetLastError() != ERROR_ALREADY_EXISTS:
        return mutex
    elif allow_multiple:
        return win32event.OpenMutex(win32con.SYNCHRONIZE, False, __instance_lock_key__)


@inject.autoparams()
async def main(app: AppStartManager):
    print('Hi, there!')
    app.setup()
    await app.run()


def get_args():
    parser = argparse.ArgumentParser(description="App, that inverts colors when you opens blinding white windows")
    parser.add_argument('--allow-multiple', '-m',
                        action='store_true',
                        help="Disable single-instance check")
    return parser.parse_args()


def bootstrap():
    args = get_args()
    lock = lock_instance(args.allow_multiple)
    if not lock:
        print("WARNING: Program already started!")
        return
    run(main())


if __name__ == '__main__':
    bootstrap()
