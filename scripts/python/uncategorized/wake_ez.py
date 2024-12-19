from pynput.keyboard import Key, Controller
from time import sleep

keyboard = Controller()
minutes = 13
seconds = minutes * 60

sleep(seconds)
keyboard.press(Key.enter)
keyboard.release(Key.enter)
