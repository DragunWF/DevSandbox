from rich import print

players = []


def solve(turn):
    print(players[turn % len(players)])


def add_players():
    players_to_add = 4
    for i in range(players_to_add):
        players.append(f"Player {i + 1}")


if __name__ == "__main__":
    add_players()
    solve(63)
