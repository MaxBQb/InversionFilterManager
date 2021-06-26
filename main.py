import active_window_checker
from logic import FilterStateController


def main():
    print(f'Hi, there!')
    active_window_checker.main(FilterStateController().on_active_window_switched)


if __name__ == '__main__':
    main()
