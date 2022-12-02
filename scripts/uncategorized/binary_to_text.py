import sys
from rich import print


def main(user_input: list):
    output = []
    user_input.pop(0)

    for byte in user_input:
        reversed_byte = [i for i in byte]
        reversed_byte.reverse()

        place, sum = 1, 0
        for digit in reversed_byte:
            sum += int(digit) * place
            place *= 2

        output.append(chr(sum))

    print("".join(output))


if __name__ == "__main__":
    main(sys.argv)
