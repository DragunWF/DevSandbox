import sys
from rich import print


def main(user_input: list):
    output = []
    user_input.pop(0)

    for byte in user_input:
        reversed_byte = [i for i in byte]
        reversed_byte.reverse()

        place, result = 1, 0
        for digit in reversed_byte:
            result += int(digit) * place
            place *= 2

        output.append(chr(result))

    print("".join(output))


if __name__ == "__main__":
    main(sys.argv)
