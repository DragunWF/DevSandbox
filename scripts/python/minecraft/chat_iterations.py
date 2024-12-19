from pynput.keyboard import Key, Controller
from time import sleep

keyboard = Controller()
iterations = 100


def send_message(content):
    keyboard.type(content)
    keyboard.press(Key.enter)
    keyboard.release(Key.enter)


def open_chat():
    keyboard.press("t")
    keyboard.release("t")


def main():
    open_chat()
    sleep(0.3)
    send_message("Executing chat script...")
    sleep(1)

    for x in range(iterations):
        sleep(0.01)
        keyboard.type(f"Iteration: {x + 1}")
        sleep(0.01)
        send_message()


sleep(5)
main()
