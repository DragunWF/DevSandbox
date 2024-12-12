from rich import print

# Define the binary string
# "11100101010100010101001010010101001010"
# "10011001111000100010010010000100"
binary_string = "11100101010100010101001010010101001010"

# Define block size
block_size = 8

# Split the binary string into blocks


def split_into_blocks(binary_string, block_size):
    return [binary_string[i:i + block_size] for i in range(0, len(binary_string), block_size)]

# Convert binary blocks to integers and calculate the arithmetic checksum
# Handle carry-over bits and apply 1's complement


def calculate_checksum(binary_string, block_size):
    blocks = split_into_blocks(binary_string, block_size)
    # Sum the decimal values of the blocks
    total = sum(int(block, 2) for block in blocks)

    # Handle carry-over bits by wrapping around
    while total > 0xFF:  # While total exceeds 8 bits (255 in decimal)
        carry = total >> 8  # Get the carry bits (excess beyond 8 bits)
        total = (total & 0xFF) + carry  # Add carry to the lower 8 bits

    # Apply 1's complement to the result
    # Apply 1's complement to fit into 8 bits
    ones_complement = (~total & 0xFF)
    return ones_complement


def main():
    # Main execution
    blocks = split_into_blocks(binary_string, block_size)
    checksum = calculate_checksum(binary_string, block_size)

    # Output results
    print("Blocks:", blocks)
    print("Checksum (1's complement):", bin(checksum)[2:].zfill(8))


if __name__ == "__main__":
    main()
