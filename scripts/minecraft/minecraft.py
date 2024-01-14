from time import sleep


def main() -> None:
    minutes = 0
    print("Program starting...")
    while True:
        sleep(60)
        minutes += 1
        print(f"Minutes Passed: {minutes}")


main()
