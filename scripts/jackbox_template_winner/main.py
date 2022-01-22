from rich.console import Console

console = Console()
current_game = ""


def write_new_title():
    game_title = input("Game Title: ").lower()


def input_line():
    global current_game
    output = ""
    if not current_game:
        write_new_title()
    else:
        while True:
            same_title = input("Same Game? (y/n) ").lower().strip()
            if same_title == "y" or same_title == "yes":
                pass
            elif same_title == "n" or same_title == "no":
                write_new_title()
            else:
                console.print("Invalid Option")


def main():
    output = ""
    lines = []

    while True:
        try:
            session_number = int(input("Enter session number: "))
            lines.append(f"Jackbox Play Session #{session_number}\n")
            lines.append("**Winners from this session:**\n")
            break
        except ValueError:
            console.print("Invalid session number!")

    while True:
        line_input = input_line()
        lines.append(line_input)
        break

    for line in lines:
        output += f"{line}\n"

    with open("output.txt", "w") as file:
        file.write(output)

    return output


console.print(main())
