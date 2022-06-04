import random
from rich import print

games_count = 10000
player_one_wins = 0
player_two_wins = 0


def play_game(player_one_playing: bool):
    global player_one_wins, player_two_wins

    flips = 10 if player_one_playing else 100
    heads_flipped = 0

    for i in range(flips):
        chance = random.randint(1, 2)
        if chance == 1:
            heads_flipped += 1

    if heads_flipped >= flips / 2:
        if player_one_playing:
            player_one_wins += 1
        else:
            player_two_wins += 1


def main():
    player_one_playing = True
    for i in range(games_count):
        play_game(player_one_playing)
        player_one_playing = False if player_one_playing else True

    print(f"""
    Game Wins:
    Player One: {player_one_wins}
    Player Two: {player_two_wins}
    """)


if __name__ == "__main__":
    main()
