# The Pragmatic Programmer 20th Anniversary Edition - Page 100

# Following on from the previous exercise, add the ability to change those
# variable names automatically in one or more files. Remember to keep a
# backup of the originals in case something goes horribly, horribly wrong.

import re
from pathlib import Path
from exercise_12 import HOME_PATH, SOURCE_PATH, camel_case_to_snake_case


BACKUP_PATH = f"{HOME_PATH}/backup"


def main() -> None:
    source_files = get_files(Path(SOURCE_PATH))
    backup_files(source_files)
    convert_variables_to_camel_case(source_files)


def get_files(path: Path) -> list:
    return [file for file in path.iterdir() if file.is_file()]


def backup_files(files: list[Path]) -> None:
    for file in files:
        with open(f"{BACKUP_PATH}/{file.name}", "w") as backup_file:
            backup_file.write(file.read_text())
    print("Files have been backed up")


def convert_variables_to_camel_case(source_code_files: list[Path]) -> None:
    for file in source_code_files:
        code = file.read_text()
        lines = code.split("\n")
        converted_code = []

        variable_declaration_pattern = re.compile(
            r"^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*.*$"
        )
        for line in lines:
            # Contains variable declaration in line
            if variable_declaration_pattern.match(line):
                tokens = line.split("=")
                # tokens[0] is the variable name
                tokens[0] = camel_case_to_snake_case(tokens[0])
                converted_code.append(" = ".join(tokens))
            else:
                converted_code.append(line)

        file.write_text("\n".join(converted_code))

    print("Variables in source code have been converted to camelCase!")


if __name__ == '__main__':
    main()
