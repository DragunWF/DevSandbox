from rich import print

GSON_STRING = "implementation 'com.google.code.gson:gson:2.10.1'"


def main() -> None:
    times_memorized = 0
    tries = int(input("Tries: "))

    for i in range(tries):
        if is_memorized():
            times_memorized += 1
        else:
            print("Incorrect!")

    print(f"Times Memorized: {times_memorized}")


def is_memorized() -> None:
    return input("Enter GSON String: ") == GSON_STRING


if __name__ == "__main__":
    main()