from time import sleep


def main() -> None:
    minutes = 0
    print("Program starting...")
    while True:
        sleep(60)
        minutes += 1
        hours = minutes // 60
        print(f"Time Passed: H:{hours} :M{minutes % 60}")


main()
