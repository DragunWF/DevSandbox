from rich import print

binary_tests = ((91, 1011011), (173, 10101101), (151, 10010111))
hexidecimal_tests = ((91, "5B"), (541, "21D"), (173, "AD"))


def convert_to_binary(num):
    output = ""
    for i in range(8):
        output += str(num % 2)
        num //= 2
    return int(output[::-1])


def convert_to_hexadecimal(num):
    letters = ("A", "B", "C", "D", "E", "F")
    output = ""

    while num != 0:
        remainder = num % 16
        num //= 16

        if remainder >= 10:
            output += letters[int(str(remainder)[-1])]
        else:
            output += str(remainder)

    return output[::-1]


def main():
    print("Binary Tests:")
    for case in binary_tests:
        print(convert_to_binary(case[0]) == case[1])

    print("\nHexidecimal Tests")
    for case in hexidecimal_tests:
        print(convert_to_hexadecimal(case[0]) == case[1])


if __name__ == '__main__':
    main()
