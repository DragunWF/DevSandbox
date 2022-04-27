import sqlite3
import os
from .time_checker import TimeChecker
from .utils import Utils


class DatabaseTool:
    def __init__(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.__path = f"{root}\\sql\\db.sqlite3"
        self.__meeting_names = []
        self.__fill_meeting_names()

    def __fill_meeting_names(self):
        with sqlite3.connect(self.__path) as db:
            data = db.execute("SELECT name FROM meetings").fetchall()
            self.__meeting_names = [i[0] for i in data]

    def insert_meeting_with_validation(self, meeting_name: str):
        name = "_".join(meeting_name.lower().split(" "))
        if not name in self.__meeting_names:
            with sqlite3.connect(self.__path) as db:
                db.execute(f"INSERT INTO meetings (name) VALUES ({name})")
                db.commit()
        self.__fill_meeting_names()

    def insert_meeting_join_record(self):
        pass

    def insert_program_open_record(self):
        pass
