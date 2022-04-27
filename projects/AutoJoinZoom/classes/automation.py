import webbrowser
import json
from pathlib import Path
from time import sleep
from sys import exit

from .time_checker import TimeChecker
from .utils import Utils


class AutomationExecutor:
    def __init__(self):
        settings = json.loads(Path(f"{Utils.get_path()}/config/settings.json").read_text())[0]
        self.__meetings = settings["meetings"]
        self.__meetings_today = []
        self.__current_meeting = {}
        self.__inside_meeting = False
        self.__iterations = 0

    def __enter_meeting(self, meeting: dict):
        Utils.tts_print(f"Entering {meeting['name']}", color="green")
        webbrowser.open(meeting["link"])
        self.__current_meeting = meeting
        self.__inside_meeting = True
        self.__iterations = 0

    def __check_if_meeting_ended(self):
        current_hour = Utils.hour_to_int(TimeChecker.get_hour())
        end_hour = Utils.hour_to_int(self.__current_meeting["hour"]["end"])
        if current_hour > end_hour:
            self.__meetings_today.pop(self.__meetings_today.index(self.__current_meeting))
            self.__current_meeting = {}
            self.__inside_meeting = False
            self.__iterations = 0

    def __check_day_for_meetings(self):
        today = TimeChecker.get_day()

        class_days = []
        for meeting in self.__meetings:
            for day in meeting["days"]:
                class_days.append(day)

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
        Utils.colored_print(f"Your meetings today are {meetings_names}", color="yellow")

    def __check_hour_for_meeting(self):
        if not self.__meetings_today:
            raise Exception("Expected error occured: You forgot to" +
                            " call __check_day_for_meetings() first...")

        current_hour = Utils.hour_to_int(TimeChecker.get_hour())
        for meeting in self.__meetings:
            start_hour = Utils.hour_to_int(meeting["hour"]["start"])
            end_hour = Utils.hour_to_int(meeting["hour"]["end"])
            if start_hour <= current_hour <= end_hour:
                self.__enter_meeting(meeting)
                break

    def start_automation(self):
        self.__check_day_for_meetings()

        while True:
            self.__iterations += 1

            if not self.__inside_meeting:
                Utils.colored_print(
                    f"No meeting ({self.__iterations})", color="yellow")
                self.__check_hour_for_meeting()
            else:
                Utils.colored_print(f"Meeting: {self.__current_meeting['name']} ({self.__iterations})",
                                    color="red")
                self.__check_if_meeting_ended()

            if not self.__meetings_today:
                Utils.tts_print("Meeting hours are over!", color="green")
                sleep(15)
                exit()
            
            sleep(2)
