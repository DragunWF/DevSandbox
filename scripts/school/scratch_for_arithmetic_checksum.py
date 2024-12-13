from rich import print


def sum_binary(values):
    return sum([int(binary, 2) for binary in values])


def main():
    values = ['111001', '01010100', '01010100', '10100101', '01001010']
    total = sum_binary(values)
    values.append("00101110")
    print(f"Total in Decimal: {total}")
    print(f"Total in Binary: {bin(total)[2:]}")

    receiver_total = sum_binary(values)
    print(f"Receiver total: {bin(receiver_total)[2:]}")


if __name__ == '__main__':
    main()
