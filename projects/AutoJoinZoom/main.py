from time import sleep
from classes.automation import AutomationExecutor
from classes.time_checker import TimeChecker
from classes.utils import Utils


def startup_greeting():
    year = TimeChecker.get_year()
    month = TimeChecker.get_month()
    day_of_month = TimeChecker.get_day_of_month()
    day_of_week = TimeChecker.get_day()
    hour = TimeChecker.format_hour(TimeChecker.get_hour())

    Utils.colored_print(f"{month} {day_of_month} {year} | {hour} {day_of_week}",
                        color="cyan")


def main():
    startup_greeting()
    automation_bot = AutomationExecutor()
    automation_bot.start_automation()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        Utils.text_to_speech("An error has occured!")
        print(error)
        sleep(30)
