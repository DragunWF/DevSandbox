from rich import print

# Seems like I forgot to commit this one. This one was months ago
# It's unfinished but I'll keep it in the repository I guess...


def main() -> None:
    print(ipv6_abbreviation("2001:0DB8:0000:0000:0008:0800:200C:417A"))


def ipv6_abbreviation(ip):
    values = ip.split(":")
    output = []
    for value in values:
        output.append(remove_leading_zeros(value))
    return ":".join(output)


def remove_leading_zeros(s:str):
    output = ""
    index = 0
    for i in range(len(s)):
        if s[i] != "0":
            index = i
            break
    return "".join([str(i) for i in range(index, len(s))])


def convert(num):
    initial = 124
    output = ""
    for i in range(8):
        if num <= initial:
            output += "1"
            num -= initial
        else:
            output = "0"
        initial /= 2
    return output


if __name__ == "__main__":
    main()
