from asyncio import run
import inject
from bootstrap import try_request_admin_rights
from app_start import AppStartManager


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
    run(main())


if __name__ == '__main__':
    bootstrap()
