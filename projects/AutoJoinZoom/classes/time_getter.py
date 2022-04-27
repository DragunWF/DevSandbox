from datetime import datetime
from .utils import Utils


class TimeGetter:
    @staticmethod
    def get_month() -> str:
        date = Utils.get_date_string()[0]
        months = ("january", "february", "march",
                  "april", "may", "june", "september",
                  "october", "november", "december")
        return months[int(date.split("-")[1]) - 1].capitalize()

    @staticmethod
    def get_year() -> str:
        return Utils.get_date_string()[0].split("-")[0]

    @staticmethod
    def get_day_of_month() -> str:
        return Utils.get_date_string()[0].split("-")[2]

    @staticmethod
    def get_hour() -> str:
        return Utils.get_date_string()[1].split(".")[0][0:5]

    @staticmethod
    def get_day() -> str:
        days_of_week = ("sunday", "monday", "tuesday", "wednesday",
                        "thursday", "friday", "saturday")
        start, now = datetime(2022, 1, 1), datetime.now()
        duration = now - start
        return days_of_week[(duration.days - 1) % 7]
