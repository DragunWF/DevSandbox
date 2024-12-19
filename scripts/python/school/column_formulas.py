from rich import print


def main() -> None:
    for i in range(2, 10):
        print(f"b{i}*0.2+c{i}*0.2+d{i}*0.2+e{i}*0.4")


if __name__ == '__main__':
    main()
