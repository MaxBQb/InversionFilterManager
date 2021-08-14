from asyncio import run
from bootstrap import try_request_admin_rights


async def main():
    from logic import App
    from gui_utils import init_theme
    print('Hi, there!')
    app = App()
    init_theme()
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
