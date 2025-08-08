import re


def main() -> None:
    test_cases = [
        "jack.281492@ortigas-cainta.sti.edu.ph",  # True
        "test@gmail.com",  # True
        "waw@yahoo.com",  # True
        "I am grute"  # False
    ]
    for email in test_cases:
        print(is_email_valid(email))


def is_email_valid(email: str) -> bool:
    return bool(re.match(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))


if __name__ == "__main__":
    main()
