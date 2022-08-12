from asyncio import run

import inject
import win32api
import win32event
from winerror import ERROR_ALREADY_EXISTS

from app_start import AppStartManager


def lock_instance():
    from _meta import __instance_lock_key__
    mutex = win32event.CreateMutex(None, False, __instance_lock_key__)
    if win32api.GetLastError() != ERROR_ALREADY_EXISTS:
        return mutex


@inject.autoparams()
async def main(app: AppStartManager):
    print('Hi, there!')
    app.setup()
    await app.run()


def bootstrap():
    lock = lock_instance()
    if not lock:
        print("WARNING: Program already started!")
        return
    run(main())


if __name__ == '__main__':
    bootstrap()
