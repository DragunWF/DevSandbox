from rich import print


def main() -> None:
    output = set()
    for i in range(1, 20 + 1):
        if i % 3 == 0 or i % 2 == 0:
            output.add(i)
    print(output)
    print(len(output))


if __name__ == '__main__':
    main()
