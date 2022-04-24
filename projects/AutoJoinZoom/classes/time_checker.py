from datetime import datetime


class TimeChecker:
    @staticmethod
    def format_hour(hour: str) -> str:
        hour_value = int(hour.split(":")[0])
        hour_of_day = hour_value - 12 if hour_value >= 13 else hour_value
        formatted_hour = f'{hour_of_day}:{hour.split(":")[1]}'
        mid_day = "PM" if hour_value >= 12 else "AM"
        return f"{formatted_hour} {mid_day}"

    @staticmethod
    def extract_month(date: str) -> str:
        months = ("january", "february", "march",
                  "april", "may", "june", "september",
                  "october", "november", "december")
        return months[int(date.split("-")[1])].capitalize()

    @staticmethod
    def get_hour() -> str:
        now = datetime.now()
        return str(now).split()[1].split(".")[0][0:5]

    @staticmethod
    def get_day() -> str:
        days_of_week = ("sunday", "monday", "tuesday", "wednesday",
                        "thursday", "friday", "saturday")
        start, now = datetime(2022, 1, 1), datetime.now()
        duration = now - start
        return days_of_week[(duration.days - 1) % 7]
