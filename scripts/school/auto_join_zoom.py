import pyautogui
from time import sleep
from datetime import datetime
from rich.console import Console

console = Console()

meetings = {"subject": ("id", "password")}
positions = {"desktop": (1359, 746), "zoom_icon": (112, 289),
             "join_meeting": (537, 313), "meeting_id": (700, 495),
             "enter_meeting": (686, 496), "close_zoom": (1109, 41)}
actions = tuple([x for x in positions])


def input_text_field(content, input_type):
    content_type = content[0] if input_type == "meeting_id" else content[1]
    sleep(0.1)
    pyautogui.typewrite(content_type)


def enter_meeting():
    for action in actions:
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


if __name__ == "__main__":
    try:
        sleep(1)
        enter_meeting()
        console.print("Script has been executed successfully",
                      style="bold green")
    except Exception:
        console.print(Exception, style="bold red")
