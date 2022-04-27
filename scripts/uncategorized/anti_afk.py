from pynput.keyboard import Controller
from colored import fg
from time import sleep
import random

keyboard = Controller()
iteration = 0

red, blue, green, cyan, yellow, = fg("light_red"), fg(
    "light_blue"), fg("light_green"), fg("light_cyan"), fg("light_yellow")
colors = (red, blue, green, cyan, yellow)

while True:
    print(random.choice(colors) + f"Iteration: {iteration}")
    sleep(10)
    keyboard.type("t")
    iteration += 1
