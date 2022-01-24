from pynput.keyboard import Key, Controller
from time import sleep

keyboard = Controller()
iterations = 1000


def send_message():
    keyboard.press(Key.enter)
    keyboard.release(Key.enter)


def open_chat():
    keyboard.press("t")
    keyboard.release("t")


def main():
    sleep(5)
    open_chat()
    sleep(0.1)
    keyboard.type("Executing chat script...")
    sleep(0.3)
    send_message()
    sleep(1)

    for x in range(iterations):
        sleep(0.01)
        keyboard.type(f"Iteration: {x + 1}")
        sleep(0.01)
        send_message()


main()
