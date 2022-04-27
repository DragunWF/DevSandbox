import pyautogui
import keyboard
from time import sleep
from rich import print


def main():
    while True:
        if keyboard.is_pressed("p"):
            print(pyautogui.position())
            sleep(0.5)


if __name__ == "__main__":
    sleep(1)
    main()
