from rich import print

# n = 5
#     1
#    121
#   12321
#  1234321
# 123454321


def main():
    n = 5
    for i in range(1, n + 1):
        print(" " * (n - i), end="")
        for j in range(1, i * 2):
            print(j if j <= i else i - (j % i), end="")
        print()


if __name__ == "__main__":
    print()
    main()
    print()
