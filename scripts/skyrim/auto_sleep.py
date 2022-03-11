import pyautogui
import keyboard
import asyncio
from time import sleep
from sys import exit

sleep_switch = False
sleeping = False


def sleep_in_bed():
    global sleeping
    positions = {"sleep": (), "enter": ()}
    sleeping = True

    pyautogui.press("e")
    for position in tuple([x for x in positions]):
        pyautogui.click(positions[position])
        sleep(0.25)
        
    sleep(25)
    sleeping = False


def main():
    global sleep_switch
    while True:
        if keyboard.is_pressed("o"):
            sleep_switch = True
        elif keyboard.is_pressed("p"):
            sleep_switch = False
        elif keyboard.is_pressed("l"):
            exit()

        if sleep_switch:
            sleep_in_bed()
        sleep(0.025)


if __name__ == "__main__":
    main()
