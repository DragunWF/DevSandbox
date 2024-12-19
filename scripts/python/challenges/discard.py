# https://snakify.org/en/lessons/dictionaries_dicts/problems/english_latin_dict/

dictionary = {}


def ascii_value(word: str) -> int:
    return sum([ord(letter) for letter in word])


def sort_words() -> None:
    items = dictionary.items()
    for i in range(len(items) - 1):
        for j in range(len(items) - 1):
            first_val = ascii_value(items[j][1])
            second_val = ascii_value(items[j + 1][1])
            if first_val > second_val:
                items[j], items[j + 1] = items[j + 1], items[j]


def print_output(items: list) -> None:
    pass


def main() -> None:
    n = int(input())
    for i in range(n):
        values = input().split("-")
        latin = [v.strip() for v in values[1].split(",")]
        english = values[0].rstrip()
        dictionary[english] = latin
    sort_words()
    print_output()


if __name__ == "__main__":
    main()
