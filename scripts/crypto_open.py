import pyautogui
from time import sleep


def execute_clicks():
    positions = {"FirstCrypto": (), "SecondCrypto": (), "ThirdCrypto": ()}
    for position in tuple([i for i in positions]):
        pyautogui.click(positions[position])


def open_browser():
    pass


def main():
    pass


if __name__ == "__main__":
    main()
