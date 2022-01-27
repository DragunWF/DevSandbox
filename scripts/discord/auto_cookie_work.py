from pynput.keyboard import Key, Controller
from time import sleep

keyboard = Controller()

# Settings
iterations = 100
command = "!work"


def send_message():
    keyboard.press(Key.enter)
    keyboard.release(Key.enter)


def main():
    for x in range(iterations):
        keyboard.type(command)
        send_message()
        sleep(60)


sleep(3)
main()
