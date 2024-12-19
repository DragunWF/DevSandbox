from time import sleep

PLAYTIME_PATH = r"E:\DevStuff\Repositories\Mini-Scripts\scripts\minecraft\minutes_played.txt"
minutes = 0


def get_minutes_played() -> str:
    with open(PLAYTIME_PATH, "r") as file:
        return int(file.read())


def update_minutes_played(value: int) -> None:
    with open(PLAYTIME_PATH, "w") as file:
        file.write(str(value))


def convert_hours(value: int) -> float:
    percentage = round((value % 60) / 60, 1)
    return value // 60 + percentage


def main() -> None:
    global minutes
    start_time = get_minutes_played()
    print("Program starting...")
    print(f"Hours Played: {convert_hours(get_minutes_played())}")
    while True:
        sleep(60)
        minutes += 1
        hours = minutes // 60
        if hours > 0:
            print(f"Time Passed: H:{hours} M:{minutes % 60}")
        else:
            print(f"Time Passed: M:{minutes % 60}")
        update_minutes_played(start_time + minutes)


main()
