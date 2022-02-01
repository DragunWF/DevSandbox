from pynput.keyboard import Key, Controller
from time import sleep

keyboard = Controller()
iterations = 50


def send_message(content):
    keyboard.type(content)
    keyboard.press(Key.enter)
    keyboard.release(Key.enter)


def main():
    for x in range(iterations):
        send_message(f"Iteration: {x + 1}")
        sleep(0.1)


sleep(3)
main()
