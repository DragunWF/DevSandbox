# The Pragmatic Programmer 20th Anniversary Edition - Page 65

# Implement the time parser using a scripting language and regular expressions

import re
import traceback


def main() -> None:
    test_cases = [
        {
            "value": "7:30am",
            "expected_output": True
        },
        {
            "value": "11:59pm",
            "expected_output": True
        },
        {
            "value": "12:00AM",
            "expected_output": True
        },
        {
            "value": "14:45",
            "expected_output": True
        },
        {
            "value": "08:05",
            "expected_output": True
        },
        {
            "value": "8:30",
            "expected_output": False
        },
        {
            "value": "13:45pm",
            "expected_output": False
        },
        {
            "value": "25:30",
            "expected_output": False
        },
        {
            "value": "10-30am",
            "expected_output": False
        },
        {
            "value": "12:60",
            "expected_output": False
        }
    ]
    for test_case in test_cases:
        print(f"Test Case: {test_case['value']}")
        assert is_valid_time(
            test_case["value"]) == test_case["expected_output"]
    print("All test cases have passed!")


def is_valid_time(time: str) -> bool:
    try:
        time = time.lower()  # Case insensitivity
        regex_12hr = r"^(1[0-2]|[1-9]):([0-5][0-9])(am|pm)$"
        regex_24hr = r"^([01][0-9]|2[0-3]):([0-5][0-9])$"

        if re.match(regex_12hr, time):
            print("Time given is in the normal time format!")
            return True
        if re.match(regex_24hr, time):
            print("Time given is in military time format!")
            return True

        print("Time is invalid!")
        return False
    except Exception:
        print(traceback.format_exc())
        return False


if __name__ == '__main__':
    main()
