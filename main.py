from asyncio import run

import inject
import win32api
import win32event
from winerror import ERROR_ALREADY_EXISTS

from app_start import AppStartManager
from uac import try_request_admin_rights


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
    result = try_request_admin_rights()
    if result:
        return
    if result is None:
        print("WARNING: Without administrator rights some features may not work properly!")
    lock = lock_instance()
    if not lock:
        print("WARNING: Program already started!")
        return
    run(main())


if __name__ == '__main__':
    bootstrap()
