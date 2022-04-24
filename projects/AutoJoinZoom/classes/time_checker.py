from datetime import datetime


class TimeChecker:
    @staticmethod
    def check_time():
        pass

    @staticmethod
    def check_hour() -> str:
        now = datetime.now()
        return str(now).split()[1].split(".")[0][0:5]

    @staticmethod
    def check_day() -> str:
        days_of_week = ("sunday", "monday", "tuesday", "wednesday",
                        "thursday", "friday", "saturday")
        start, now = datetime(2022, 1, 1), datetime.now()
        duration = now - start
        return days_of_week[(duration.days - 1) % 7]
