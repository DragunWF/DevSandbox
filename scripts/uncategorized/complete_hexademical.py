import sys
from rich import print


def main():
    arguments = sys.argv[1:]
    output = [f"0x{x}" for x in arguments]
    print(" ".join(output))


if __name__ == "__main__":
    main()
