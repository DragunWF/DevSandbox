from rich import print
from string import ascii_uppercase


def main() -> None:
    print(create_cipher_map("COLLEGE"))

    print(encrypt("A B C D E F G H I J K L M N O P Q R S T U V W X Y Z", "KRYPTOS"))
    print(encrypt("UNIVERSITY", "COLLEGE"))  # UMFVGRSFTY
    print(encrypt("Knowledge is Power", "KRYPTOS"))  # IlmWjbaEb GQ NmWbp
    print(encrypt("zljeft dtOT", "secret"))  # ZOMBIE HERE


def encrypt(plain_text: str, keyword: str) -> str:
    cipher_map = create_cipher_map(keyword)
    output = ""
    for char in plain_text.upper():
        if not char in cipher_map:
            output += char
            continue
        ascii_pos = ascii_uppercase.index(char)
        output += cipher_map[ascii_pos]
    return output


def create_cipher_map(keyword: str) -> str:
    cipher_map = []
    for char in (keyword.upper() + ascii_uppercase):
        if not char in cipher_map:
            cipher_map.append(char)
    return cipher_map


if __name__ == "__main__":
    main()
