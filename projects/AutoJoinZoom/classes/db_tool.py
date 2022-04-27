import sqlite3
import os
from .time_checker import TimeChecker
from .utils import Utils


class DatabaseTool:
    def __init__(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.__path = f"{root}\\sql\\db.sqlite3"
        self.__meeting_names = []

        with sqlite3.connect(self.__path) as db:
            names = db.execute("SELECT name FROM meetings").fetchall()
            self.__meeting_names = [i for i in names]

    def __check_if_meeting_exists(self, meeting_name: str) -> bool:
        with sqlite3.connect(self.__path) as db:
            query = f"SELECT name FROM meetings WHERE meeting_name = {meeting_name}"
            return bool(db.execute(query).fetchall())

    def insert_meeting_with_validation(self, meeting_name: str):
        name = "_".join(meeting_name.lower().split(" "))
        if not DatabaseTool.__check_if_meeting_exists(name):
            with sqlite3.connect(self.__path) as db:
                db.execute(f"INSERT INTO meetings (name) VALUES ({name})")
                db.commit()

    def insert_meeting_join_record(self):
        pass

    def insert_program_open_record(self):
        pass

    def insert_record(self, record_type: str):
        tables = {"meeting_joined": "meeting_joins",
                  "program_opened": "times_program_opened"}
        date = Utils.get_date_string()
        hour = TimeChecker.format_hour(TimeChecker.get_hour())

        with sqlite3.connect(self.__path) as db:
            db.execute(
                f"INSERT INTO {tables[record_type]} (date, hour) VALUES ({date} {hour})")
            db.commit()
