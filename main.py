from asyncio import run


async def main():
    from logic import App
    print('Hi, there!')
    app = App()
    app.run()
    print("I'm async")


if __name__ == '__main__':
    run(main())
