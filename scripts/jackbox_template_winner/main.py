from rich.console import Console
from time import sleep

console = Console()
current_game = ""
game_number = 1


def write_new_winner():
    global game_number
    game_number += 1
    return input("Game Winner: ").lower()


def write_new_title():
    return input("Game Title: ").lower()


def write_template_line():
    global current_game, game_number
    output = ["", False]  # Template line, is_game_ending

    if not current_game:
        game_title = f"**{write_new_title()}:**"
        game_winner = f"`Game {game_number}:` @{write_new_winner()}"
        output[0] = f"{game_title}\n{game_winner}".title()
        current_game = game_title
    else:
        while True:
            same_title = input("Same Game? (y/n) ").lower().strip()
            if same_title == "y" or same_title == "yes":
                game_winner = f"`Game {game_number}:` @{write_new_winner()}"
                output[0] = f"{game_winner}".title()
                break
            elif same_title == "n" or same_title == "no":
                game_title = f"**{write_new_title()}:**"
                game_winner = f"`Game {game_number}:` @{write_new_winner()}"
                output[0] = f"\n{game_title}\n{game_winner}".title()
                current_game = game_title
                break
            else:
                console.print("Invalid Option")

    while True:
        option = input("Game ending? (y/n) ").lower().strip()
        if option == "y" or option == "yes":
            output[1] = True
            break
        elif option == "n" or option == "no":
            break
        else:
            console.print("Invalid Option")

    return output


def main():
    output = ""
    lines = []

    while True:
        try:
            session_number = int(input("Enter session number: "))
            lines.append(f">>> Jackbox Play Session #{session_number}\n")
            lines.append("**Winners from this session:**\n")
            break
        except ValueError:
            console.print("Invalid session number!")

    while True:
        line_input, game_ending = write_template_line()
        lines.append(line_input)
        if game_ending:
            break

    lines.append("\nThanks for Playing!")

    for line in lines:
        output += f"{line}\n"

    with open("scripts/jackbox_template_winner/output.txt", "w") as file:
        file.write(output)

    return output


console.print(main())
sleep(15)
