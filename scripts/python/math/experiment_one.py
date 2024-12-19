import math
from rich import print


def main():
    while True:
        a = int(input("Fraction 1 Denominator: "))
        b = int(input("Fraction 1 Numerator: "))
        x = int(input("Fraction 2 Denominator: "))
        y = int(input("Fraction 2 Numerator: "))

        maxDenominator, minDenominator = max(a, x), min(a, x)
        for n in range(1, 100000):
            r = (maxDenominator * n) % minDenominator
            if r == 0:
                print(f"""
                n = {n}
                r = {a * n}/{b * n} + {x * n}/{a * n}
                """)
                break

        choice = input("continue? type 'n' to quit ").lower().strip()
        if choice == "n" or choice == "no":
            break


if __name__ == "__main__":
    main()
