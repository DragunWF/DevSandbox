# The Pragmatic Programmer 20th Anniversary Edition - Page 99

# You're rewriting an application that used to use YAML as a configuration
# language. Your company has now standardized JSON, so you have a bunch
# of .yaml files that need to be turned into .json. Write a script that takes a
# directory and converts each .yaml file itno the corresponding .json file (so
# database.yaml becomes database.json, and the contents of the values are valid JSON)

import traceback
import json
import yaml

from pathlib import Path

HOME_PATH = "scripts/python/pragmatic_programmer_exercises/exercise_11/"
YAML_PATH = f"{HOME_PATH}/yaml"
JSON_PATH = f"{HOME_PATH}/json"


def main() -> None:
    try:
        yaml_files = get_file_names(Path(YAML_PATH))
        converted_yaml_data = []

        # Append YAML file contents as a dictionary to the data list
        for file_name in yaml_files:
            with open(f"{YAML_PATH}/{file_name}", "r") as file:
                YAML_CONTENTS = file.read()
                converted_yaml_data.append(yaml_to_dict(YAML_CONTENTS))

        # Write JSON files to JSON directory
        for i, data in enumerate(converted_yaml_data):
            with open(f"{JSON_PATH}/data_{i + 1}.json", "w") as file:
                file.write(dict_to_json(data))

        print("Files have been converted to JSON")
    except Exception as e:
        print(
            f"An unexpected error occurred while converted YAML to JSON: {e}"
        )
        print(traceback.format_exc())


def get_file_names(directory: Path) -> list[str]:
    return [file.name for file in directory.iterdir() if file.is_file()]


def yaml_to_dict(file_contents: str) -> dict:
    return yaml.safe_load(file_contents)


def dict_to_json(data: dict) -> None:
    return json.dumps(data, indent=4)


if __name__ == '__main__':
    main()
