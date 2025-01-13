# The Pragmatic Programmer 20th Anniversary Edition - Page 112

def main() -> None:
    series = []
    current_num = 0
    while current_num <= 100:
        series.append(current_num)
        current_num += 5
    print(f"Series: {series}")
    print(f"The amount of numbers in the series is {len(series)}")


if __name__ == '__main__':
    # Output:
    # Series: [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
    # The amount of numbers in the series is 21
    main()
