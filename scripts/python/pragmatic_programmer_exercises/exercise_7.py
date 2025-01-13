# The Pragmatic Programmer 20th Anniversary Edition - Page 65

# Implement a parser for the BNF grammar in the previous exercise using a
# PEG parser generator in the language of your choice. The output should
# be an integer containing the number of minutes past midnight

import traceback
from lark import Lark


def main() -> None:
    grammar = """
start: military_time | normal_time

military_time: hour_24 ":" minutes
normal_time: hour_12 ":" minutes time_of_day

time_of_day: "am" | "pm" | "AM" | "PM"
hour_24: /([01][0-9]|2[0-3])/  // Matches 00-23
hour_12: /(0?[1-9]|1[0-2])/    // Matches 1-12
minutes: /[0-5][0-9]/          // Matches 00-59

%import common.WS
%ignore WS
"""
    parser = Lark(grammar)

    try:
        user_input_time = input("Input time: ")
        parse_tree = parser.parse(user_input_time)
        print(parse_tree.pretty())
        print(
            f"Minutes passed midnight: {get_minutes_pass_midnight(user_input_time)}"
        )
    except Exception as e:
        print(f"Invalid time format! {e}")
        print(traceback.format_exc())


def get_minutes_pass_midnight(time: str) -> int:
    time = time.lower()  # Case insensitivity
    is_12_hour_format = "am" in time or "pm" in time

    if is_12_hour_format:
        # Strips "am" or "pm" from the time string
        formatted_time = time[0:len(time) - 2].split(":")
        hours, minutes = get_time(formatted_time)

        if "pm" in time:
            hours += 12
        return get_minutes(hours, minutes)

    # Military time
    formatted_time = time.split(":")
    hours, minutes = get_time(formatted_time)
    return get_minutes(hours, minutes)


def get_time(formatted_time: list[str]) -> tuple[int, int]:
    if not type(formatted_time) == list or len(formatted_time) != 2:
        raise Exception(f"{formatted_time} is invalid!")
    return int(formatted_time[0]), int(formatted_time[1])


def get_minutes(hours: int, minutes: int) -> int:
    return hours * 60 + minutes


if __name__ == "__main__":
    main()
