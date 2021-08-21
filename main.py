import inject
from logic import App
from asyncio import run
from bootstrap import try_request_admin_rights


@inject.autoparams()
async def main(app: App):
    from gui_utils import init_theme
    print('Hi, there!')
    init_theme()
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
