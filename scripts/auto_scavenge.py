from pynput.keyboard import Key, Controller
from time import sleep

keyboard = Controller()

# Settings
iterations = 100
command = "d!e scavenge"


def send_message():
    keyboard.press(Key.enter)
    keyboard.release(Key.enter)


def main():
    for x in range(iterations):
        sleep(1.5)
        keyboard.type(command)
        send_message()


sleep(3)
main()
