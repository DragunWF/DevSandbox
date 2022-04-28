import webbrowser
import json
from pathlib import Path
from time import sleep
from sys import exit

from .time_getter import TimeGetter
from .utils import Utils


class AutomationExecutor:
    def __init__(self, database_tool: object):
        settings = json.loads(Path(f"{Utils.get_path()}/config/settings.json").read_text())[0]
        self.__meetings = settings["meetings"]
        self.__meetings_today = []
        self.__current_meeting = {}
        self.__inside_meeting = False
        self.__iterations = 0
        self.__db_tool = database_tool

        self.__check_for_name_duplicates()

    def __check_for_name_duplicates(self):
        meeting_names = tuple([i["name"] for i in self.__meetings])
        for name in meeting_names:
            if meeting_names.count(name) > 1:
                raise Exception("You cannot have duplicate meeting names!")

    def __enter_meeting(self, meeting: dict):
        Utils.tts_print(f"Entering {meeting['name']}", color="green")
        webbrowser.open(meeting["link"])
        self.__current_meeting = meeting
        self.__inside_meeting = True
        self.__iterations = 0
        self.__db_tool.insert_meeting_join_record(meeting["name"])

    def __check_if_meeting_ended(self):
        current_hour = Utils.hour_to_int(TimeGetter.get_hour())
        end_hour = Utils.hour_to_int(self.__current_meeting["hour"]["end"])
        if current_hour > end_hour:
            self.__meetings_today.pop(self.__meetings_today.index(self.__current_meeting))
            self.__current_meeting = {}
            self.__inside_meeting = False
            self.__iterations = 0

    def __check_day_for_meetings(self):
        today = TimeGetter.get_day()

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

        meeting_names = ", ".join([i["name"] for i in self.__meetings_today])
        Utils.colored_print(f"Your meetings today are {meeting_names}", color="yellow")

    def __check_meetings_left_today(self):
        if not self.__meetings_today:
            raise Exception("Call __check_day_for_meetings() first before this function!")

        meetings_left_today = []
        current_hour = Utils.hour_to_int(TimeGetter.get_hour())
        for meeting in self.__meetings_today:
            end_hour = Utils.hour_to_int(meeting["hour"]["end"])
            if end_hour > current_hour:
                meetings_left_today.append(meeting)
        self.__meetings_today = meetings_left_today

        meeting_count = len(self.__meetings_today)
        if meeting_count:
            meeting_string = "meetings" if meeting_count > 1 else "meeting"
            Utils.colored_print(f"You have {meeting_count} {meeting_string} left today",
                                color="green")
        else:
            Utils.colored_print("You have no more meetings left today!",
                                color="green")

    def __check_hour_for_meeting(self):
        current_hour = Utils.hour_to_int(TimeGetter.get_hour())
        for meeting in self.__meetings_today:
            start_hour = Utils.hour_to_int(meeting["hour"]["start"])
            end_hour = Utils.hour_to_int(meeting["hour"]["end"])
            if start_hour <= current_hour <= end_hour:
                self.__enter_meeting(meeting)
                break

    def start_automation(self):
        self.__check_day_for_meetings()
        self.__check_meetings_left_today()

        while True:
            self.__iterations += 1

            if not self.__meetings_today:
                Utils.tts_print("Meeting hours are over!", color="green")
                sleep(15)
                exit()

            if not self.__inside_meeting:
                Utils.colored_print(f"No meeting ({self.__iterations})", color="yellow")
                self.__check_hour_for_meeting()
            else:
                Utils.colored_print(f"Meeting: {self.__current_meeting['name']} ({self.__iterations})",
                                    color="red")
                self.__check_if_meeting_ended()

            sleep(3)
