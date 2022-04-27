import webbrowser
import json
from pathlib import Path
from time import sleep
from sys import exit

from .time_checker import TimeChecker
from .utils import Utils


class AutomationExecutor:
    def __init__(self):
        settings = json.loads(Path(Utils.get_path()).read_text())[0]
        self.__meetings = settings["meetings"]
        self.__meetings_today = []
        self.__current_meeting = {}
        self.__inside_meeting = False

    def __enter_zoom_class(self, meeting: dict):
        Utils.tts_print(f"Entering {meeting['name']}", color="yellow")
        webbrowser.open(meeting["link"])
        self.__inside_meeting = True

    def __check_day_for_meetings(self):
        today = TimeChecker.get_day()

        class_days = []
        for meeting in self.__meetings:
            class_days.append(meeting["days"])

        if not today in set(class_days):
            Utils.tts_print("You have no classes today!", color="green")
            sleep(15)
            exit()

        for meeting in self.__meetings:
            for day in meeting["days"]:
                if today == day:
                    self.__meetings_today.append(meeting)
                    break

        meetings_names = ", ".join([i["name"] for i in self.__meetings_today])
        Utils.colored_print(f"Your meetings today are {meetings_names.strip()}")

    def __check_hour_for_meeting(self):
        if not self.__meetings_today:
            raise Exception("Expected error occured: You forgot to" +
                            " call __check_day_for_meetings() first...")

        current_hour = Utils.convert_hour_to_int(TimeChecker.get_hour())
        for meeting in self.__meetings:
            meeting_hour = Utils.convert_hour_to_int(meeting["hour"]["start"])

    def start_automation(self):
        self.__check_day_for_meetings()

        while True:
            self.__check_hour_for_meeting()
