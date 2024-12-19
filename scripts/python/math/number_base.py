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


def test(test_cases, func):
    for i in range(len(test_cases)):
        result = func(test_cases[i][0])
        expected = test_cases[i][1]
        print(f"Test Case #{i + 1}: Result: {result} | Success: {result == expected}")


def main():
    print("Binary Tests:")
    test(binary_tests, convert_to_binary)

    print("\nHexadecimal Tests")
    test(hexidecimal_tests, convert_to_hexadecimal)


if __name__ == '__main__':
    main()
