import pyautogui
from time import sleep
from datetime import datetime
from rich.console import Console

console = Console()
meetings = {"subject1": ("id", "password"), "subject2": (
    "id", "password"), "subject3": ("id", "password")}


def input_text_field(content, input_type):
    content_type = content[0] if input_type == "meeting_id" else content[1]
    sleep(0.1)
    pyautogui.typewrite(content_type)


def enter_meeting():
    positions = {"desktop": (1359, 746), "zoom_icon": (112, 289),
                 "join_meeting": (537, 313), "meeting_id": (700, 495),
                 "enter_meeting": (686, 496), "close_zoom": (1109, 41)}

    for action in tuple([x for x in positions]):
        delay = 0.8
        if action != "zoom_icon":
            if action in ("meeting_id", "enter_meeting"):
                input_text_field(meetings["subject"], action)
                delay = 1.5
            sleep(0.1)
            pyautogui.click(positions[action])
        else:
            pyautogui.doubleClick(positions[action])

        sleep(delay)


def check_time():
    day_of_week = ("sunday", "monday", "tuesday", "wednesday",
                   "thursday", "friday", "saturday")
    start = datetime(2022, 1, 1)
    now = datetime.now()
    duration = now - start

    day = day_of_week[(duration.days - 1) % 7]
    hour = str(now).split()[1].split(".")[0]

    return day, hour


def main():
    while True:
        pass


if __name__ == "__main__":
    try:
        sleep(1)
        enter_meeting()
        console.print("Script has been executed successfully",
                      style="bold green")
    except Exception:
        console.print(str(Exception), style="bold red")

# 12:00:00
# 12:55:00
# 13:55:00
