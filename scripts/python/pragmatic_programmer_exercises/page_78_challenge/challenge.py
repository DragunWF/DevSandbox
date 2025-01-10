# The Pragmatic Programmer 20th Anniversary Edition
# Page 78 Challenge - The Power of Plain Text

# Design a small address book database (name, phone number, and so on)
# using a straightforward binary representation in your language of choice
# Do this before reading the rest of this challenge
# - Translate that format into a plain-text format using XML or JSON
# - For each version, add a new, variable-length field called directions in
#   which you might enter directions to each person's house
# What issues come up regarding versioning and extensibility? Which form
# was easier to modify? What about converting existing data?

import json


class AddressBook:
    data = []

    def __init__(self, name: str, phone_number: str, directions: str):
        self.name = name
        self.phone_number = phone_number
        self.directions = directions


def convert_list_to_dict(data: list[AddressBook]) -> dict:
    output = []
    for address_book in data:
        output.append({"name": address_book.name,
                      "phone_number": address_book.phone_number,
                       "directions": address_book.directions})
    return output


def save_file_to_json(data: list[dict], file_location: str) -> None:
    if not file_location.endswith(".json"):
        raise ValueError("File location must end with .json")

    with open(file_location, "w") as file:
        json.dump(data, file, indent=4)


def add_dummy_data() -> None:
    AddressBook.data.append(AddressBook("Sicily", "0963 812 5123", "Right"))
    AddressBook.data.append(AddressBook("Manila", "0923 142 2524", "Left"))
    AddressBook.data.append(AddressBook("Antipolo", "0847 441 9501", "Middle"))


def main() -> None:
    SAVE_FILE_LOCATION = "./scripts/python/pragmatic_programmer_exercises/page_78_challenge/data.json"

    add_dummy_data()
    print(f"Addresses: {AddressBook.data}")

    serialized_addresses = convert_list_to_dict(AddressBook.data)
    print(f"Addresses in dict: {serialized_addresses}")

    save_file_to_json(serialized_addresses, SAVE_FILE_LOCATION)
    print(
        f"Addresses exported to a json file\nFile Location: {SAVE_FILE_LOCATION}"
    )


if __name__ == '__main__':
    main()
