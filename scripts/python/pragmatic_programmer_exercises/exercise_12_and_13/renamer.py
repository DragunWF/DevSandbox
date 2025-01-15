# The Pragmatic Programmer 20th Anniversary Edition - Page 100

# Your team initially chose to use camelCase names for variables, but then changed
# their collective mind and switched to snake_case. Write a script that scans all
# the source files for camelCase names and reports on them.

from pathlib import Path

HOME_PATH = "scripts/python/pragmatic_programmer_exercises/exercise_12_and_13/"
SOURCE_PATH = f"{HOME_PATH}/source"


def main() -> None:
    directory = Path(SOURCE_PATH)
    source_files = [file for file in directory.iterdir() if file.is_file()]

    for file in source_files:
        new_file_name = camel_case_to_snake_case(file.name)
        new_path = file.with_name(new_file_name)
        file.rename(new_path)
    print("Files have been renamed!")


def camel_case_to_snake_case(name: str) -> str:
    output = ""
    for char in name:
        output += f"_{char.lower()}" if char.isupper() else char
    return output


if __name__ == '__main__':
    main()
