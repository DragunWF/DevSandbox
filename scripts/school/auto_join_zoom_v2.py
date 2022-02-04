import pyautogui
from sys import exit
from time import sleep
from datetime import datetime
from colored import fg

# This is for .exe compiling since rich has problems with pyinstaller
red, cyan, yellow, green = fg("light_red"), fg("light_cyan"), fg("light_yellow"), fg("light_green")


def pre_open_zoom():  # This is to reduce boot-up time when opening next time
    positions = {"desktop": (1359, 746), "zoom_icon": (112, 289),
                 "close_zoom": (1109, 41)}

    for action in tuple([x for x in positions]):
        if action != "zoom_icon":
            pyautogui.click(positions[action])
            sleep(0.2)
        else:
            pyautogui.doubleClick(positions[action])
            sleep(3.5)

    return "Zoom has been Pre-Opened!"


def input_text_field(content, input_type):
    content_type = content[0] if input_type == "meeting_id" else content[1]
    sleep(0.1)
    pyautogui.typewrite(content_type)


def enter_meeting(subject, meetings):
    positions = {"desktop": (1359, 746), "zoom_icon": (112, 289),
                 "join_meeting": (537, 313), "meeting_id": (700, 495),
                 "enter_meeting": (686, 496), "close_zoom": (1109, 41)}

    for action in tuple([x for x in positions]):
        delay = 0.3
        if action != "zoom_icon":
            if action in ("meeting_id", "enter_meeting"):
                input_text_field(meetings[subject], action)
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
    hour = str(now).split()[1].split(".")[0][0:5]

    return day, hour


def check_day(day: str):
    classes = (("monday", "wednesday"), ("tuesday", "thursday"))

    if day in ("sunday", "friday", "saturday"):
        print(green + "You have no classes today!")
        sleep(25)
        exit()

    for meeting_days in classes:
        if day in meeting_days:
            return classes.index(meeting_days)


def check_hour(hour: str):
    class_hours = (("12:00", "12:40"), ("12:55", "13:35"), ("13:55", "14:35"))
    formatted = list(map(lambda x: [int("".join(i.split(":"))) for i in x],
                         class_hours))
    hour = int("".join(hour.split(":")))

    for hours in formatted:
        if hours[0] <= hour <= hours[1]:
            return formatted.index(hours)

    return False


def main():
    meetings_one = {"subject1": ("id", "password"),
                    "subject2": ("id", "password"),
                    "subject3": ("id", "password")}
    meetings_two = {"subject1": ("id", "password"),
                    "subject2": ("id", "password"),
                    "subject3": ("id", "password")}
    meetings = (meetings_one, meetings_two)
    iteration, inside_class = 0, False

    print(yellow + pre_open_zoom())
    while True:
        time = tuple(check_time())
        meetings_index = check_day(time[0])
        subjects = tuple([x for x in meetings[meetings_index]])
        subject_index = check_hour(time[1])

        if type(subject_index) != type(False) and not inside_class:
            iteration = 0
            inside_class = True
            enter_meeting(subjects[subject_index], meetings[meetings_index])
        elif type(subject_index) == type(False):
            iteration += 1
            inside_class = False
            print(cyan + f"No subject yet... ({iteration})")

        if inside_class:
            iteration += 1
            title = " ".join(list(subjects[subject_index].split("_"))).title()
            print(red + f"Subject: {title} ({iteration})")

        sleep(10)


if __name__ == "__main__":
    try:
        sleep(1)
        main()
    except Exception:
        print(red + Exception)
        sleep(30)
