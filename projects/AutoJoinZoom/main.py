from datetime import datetime
from time import sleep
from classes.automation import AutomationExecutor
from classes.time_checker import TimeChecker


def startup_greeting():
    date = datetime.now().split(" ")[0]
    hour = TimeChecker.format_hour(TimeChecker.get_hour())


def main():
    startup_greeting()
    automation_bot = AutomationExecutor()
    automation_bot.start_automation()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(error)
        sleep(30)
