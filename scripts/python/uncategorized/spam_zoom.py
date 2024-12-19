from pynput.keyboard import Key, Controller
from time import sleep

keyboard = Controller()
iterations = 250


def send_message(content):
    keyboard.type(content)
    keyboard.press(Key.enter)
    keyboard.release(Key.enter)


def main():
    sleep(0.3)
    send_message("Executing chat script...")
    sleep(1)

    for x in range(iterations):
        sleep(0.01)
        send_message(f"Iteration: {x + 1}")
        sleep(0.01)


sleep(5)
main()
