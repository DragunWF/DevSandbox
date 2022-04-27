import os
import pyttsx3
from datetime import datetime
from colored import fg

voice_engine = pyttsx3.init("sapi5")
voices = voice_engine.getProperty("voices")
voice_engine.setProperty("voice", voices[0].id)


class Utils:
    @staticmethod
    def text_to_speech(text: str):
        voice_engine.say(text)
        voice_engine.runAndWait()

    @staticmethod
    def colored_print(text: str, color: str):
        formatted_color = fg(f"light_{color}") if color != "white" else fg("white")
        print(formatted_color + text)

    @staticmethod
    def tts_print(text: str, color: str):
        Utils.text_to_speech(text)
        Utils.colored_print(text, color)

    @staticmethod
    def get_path() -> str:
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        while "\\" in root:
            root = root.replace("\\", "/")
        root = "".join([i if i != ":" else f"{i}/" for i in root])

        return f"{root[0].upper()}{root[1:]}"

    @staticmethod
    def format_hour(hour: str) -> str:
        hour_value = int(hour.split(":")[0])
        hour_of_day = hour_value - 12 if hour_value >= 13 else hour_value
        formatted_hour = f'{hour_of_day}:{hour.split(":")[1]}'
        mid_day = "PM" if hour_value >= 12 else "AM"
        return f"{formatted_hour} {mid_day}"

    @staticmethod
    def get_date_string() -> str:
        return str(datetime.now()).split(" ")
    
    @staticmethod
    def hour_to_int(hour: str) -> int:
        return int("".join(hour.split(":")))
