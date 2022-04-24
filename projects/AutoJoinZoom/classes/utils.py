import pyttsx3
from colored import fg


class Utils:
    @staticmethod
    def text_to_speech(text):
        pass

    @staticmethod
    def colored_print(text, color):
        pass

    @staticmethod
    def tts_print(text, color):
        Utils.text_to_speech(text)
        Utils.colored_print(text, color)
