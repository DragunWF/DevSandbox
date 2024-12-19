from rich import print


def split_into_blocks(text, direction="left"):
    """
    Splits a string into 8-character blocks and includes the last block even if it's less than 8 characters.

    Args:
        text (str): The input string to be split.
        direction (str): The direction of splitting, either 'left' or 'right'.
                        'left' splits the string from left to right.
                        'right' splits the string from right to left.

    Returns:
        list: A list of 8-character blocks.
    """
    block_size = 8
    if direction == "left":
        blocks = [text[i:i + block_size]
                  for i in range(0, len(text), block_size)]
    elif direction == "right":
        blocks = [text[max(0, len(text) - i - block_size):len(text) - i]
                  for i in range(0, len(text), block_size)][::-1]
    else:
        raise ValueError("Invalid direction. Choose 'left' or 'right'.")

    return blocks


def main() -> None:
    data = "11100101010100010101001010010101001010"
    print("8 bits each (Do padding for bytes with missing bits)")
    print(split_into_blocks(data))
    print(split_into_blocks(data, "right"))

    handout_data = "10011001111000100010010010000100"
    print("Data from handout")
    print(split_into_blocks(handout_data))


if __name__ == '__main__':
    main()
