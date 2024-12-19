from rich import print


# XOR function
def xor(a, b):
    result = []
    for i in range(1, len(b)):
        if a[i] == b[i]:
            result.append('0')
        else:
            result.append('1')
    return ''.join(result)


# Modulo-2 division with quotient tracking
def mod2div_with_quotient(dividend, divisor):
    pick = len(divisor)
    tmp = dividend[0:pick]
    quotient = []  # To store quotient bits

    while pick < len(dividend):
        if tmp[0] == '1':
            quotient.append('1')  # Record '1' in quotient for division step
            tmp = xor(divisor, tmp) + dividend[pick]
        else:
            quotient.append('0')  # Record '0' in quotient for no division
            tmp = xor('0' * pick, tmp) + dividend[pick]

        pick += 1

    # Last XOR for the remaining bits
    if tmp[0] == '1':
        quotient.append('1')
        tmp = xor(divisor, tmp)
    else:
        quotient.append('0')
        tmp = xor('0' * pick, tmp)

    remainder = tmp  # Remaining bits after division
    return ''.join(quotient), remainder


# Encode data by appending the remainder
def encodeData(data, key):
    l_key = len(key)
    appended_data = data + '0' * (l_key - 1)
    quotient, remainder = mod2div_with_quotient(appended_data, key)

    # Append the remainder to the original data
    codeword = data + remainder
    print("Quotient : ", quotient)
    print("Remainder : ", remainder)
    print("Encoded Data (Data + Remainder) : ", codeword)


# Driver code
data = "110110"
key = "1011"
encodeData(data, key)
