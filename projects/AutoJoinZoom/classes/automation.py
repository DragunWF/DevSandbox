import pyautogui
import json
from pathlib import Path
from time import sleep
from sys import exit

from .time_checker import TimeChecker
from .utils import Utils


class AutomationExecutor:
    def __init__(self):
        config = json.loads(Path(Utils.get_path()).read_text())[0]
        self.positions = {"desktop": (1359, 746), "zoom_icon": (112, 289),
                          "join_meeting": (537, 313), "meeting_id": (700, 495),
                          "enter_meeting": (686, 496), "close_zoom": (1109, 41)}
        self.meetings = config["meetings"]
        self.meeting_days = config["meeting_days"]

    def __input_text_field(self, info, info_type):
        content_type = info[0] if info_type == "meeting_id" else info[1]
        sleep(0.1)
        pyautogui.typewrite(content_type)

    def __enter_zoom_class(self):
        automation_steps = tuple([x for x in self.positions])

        for action in automation_steps:
            delay = 0.3
            if action != "zoom_icon":
                if action in ("meeting_id", "enter_meeting"):
                    # self.input_text_field(meetings[subject], action)
                    delay = 1.5
                sleep(0.1)
                pyautogui.click(self.positions[action])
            else:
                pyautogui.doubleClick(self.positions[action])

        sleep(delay)

    def __check_day_for_meeting(self):
        today = TimeChecker.get_day()
        class_days = self.meeting_days["classes"]
        no_class_days = self.meeting_days["no_classes"]

        if today in class_days and today in no_class_days:
            Utils.tts_print("An expected error has occured!", color="red")
            raise Exception(
                'Check your config, you have a day that exists both classes and no classes lists in your "meeting_days" object')

        if today in no_class_days:
            Utils.tts_print("You have no classes today!", color="green")
            sleep(15)
            exit()
        else:
            Utils.colored_print("There are classes today...", color="yellow")

    def __check_hour_for_meeting(self):
        pass

    def start_automation(self):
        pass
