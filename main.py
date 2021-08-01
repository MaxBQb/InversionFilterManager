from asyncio import run


async def main():
    from logic import App
    from gui_utils import init_theme
    print('Hi, there!')
    app = App()
    init_theme()
    app.run()
    print("I'm async")


if __name__ == '__main__':
    run(main())
