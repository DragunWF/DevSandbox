import sqlite3
from datetime import datetime
from tabulate import tabulate
from rich import print


def int_input(prompt: str) -> int:
    try:
        return int(input(f"{prompt}: "))
    except ValueError:
        print("Please enter a valid value!")
        return int_input(prompt)


def main() -> None:
    savings = int_input("How much did you get for today?")
    expenses = int_input("How much did you spend today?")
    balance = savings - expenses
    print(f"Your balance for today: {balance}")
    


if __name__ == "__main__":
    main()