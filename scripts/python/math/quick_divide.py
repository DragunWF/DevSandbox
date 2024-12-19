from rich import print


def main() -> None:
    while True:
        nums = [int(x) for x in input(
            "Enter two numbers separated by a space: ").split(" ")]
        result = nums[0] // nums[1]
        remainder = nums[0] % nums[1]
        print(f"{nums[0]} / {nums[1]} = {result}",
              end="\n" if not remainder else f" r: {remainder}\n")


if __name__ == "__main__":
    main()
