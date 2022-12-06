import math
from rich import print


def main():
    while True:
        try:
            r = round(eval(input()), 2)
            print(f"Result: {r}")
        except Exception:
            print("Invalid input!")


if __name__ == "__main__":
    main()
