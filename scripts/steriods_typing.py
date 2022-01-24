from pynput.keyboard import Controller
from time import sleep

keyboard = Controller()
paragraph = "If a man's wearing his pants on his head or if he says his words backwards from time to time, you know it's all laid out there for you. But if he's friendly to strangers and keeps his home spick-and-span, more often than not he's done something even his own ma couldn't forgive."


def main():
    for letter in paragraph:
        keyboard.type(letter)
        sleep(0.002)


sleep(3)
main()
