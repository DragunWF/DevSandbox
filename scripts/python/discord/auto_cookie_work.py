import random
import math
from time import sleep
from pynput.keyboard import Key, Controller
from rich.console import Console

keyboard = Controller()
console = Console()
iterations = 1000


def send_message(content):
    keyboard.type(content)
    keyboard.press(Key.enter)
    keyboard.release(Key.enter)


def main():
    colors = ("red", "green", "yellow", "blue",
              "magenta", "pink3", "cyan", "orange3")
    for x in range(iterations):
        deposited = False
        send_message("!work")
        console.print(f"Iteration: {x + 1}",
                      style=f"bold {random.choice(colors)}")
        if math.floor((x + 1) % 10) == 0:
            sleep(3)
            send_message("!dep all")
            deposited = True
        sleep(60 if not deposited else 57)


sleep(3)
main()
