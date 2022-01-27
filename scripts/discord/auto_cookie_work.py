import random
import math
from time import sleep
from pynput.keyboard import Key, Controller
from rich.console import Console

keyboard = Controller()
console = Console()

# Settings
iterations = 250
command = "!work"


def send_message():
    keyboard.press(Key.enter)
    keyboard.release(Key.enter)


def main():
    colors = ("red", "green", "yellow", "blue",
              "magenta", "red", "cyan", "orange3")
    for x in range(iterations):
        keyboard.type(command)
        send_message()
        console.print(f"Iteration: {x + 1}",
                      style=f"bold {random.choice(colors)}")
        sleep(60)
        if math.floor((x + 1) % 10) == 0:
            sleep(1)
            keyboard.type("!dep all")
            send_message()


sleep(3)
main()
