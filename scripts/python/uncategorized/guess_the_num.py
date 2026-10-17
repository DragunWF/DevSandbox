from random import randint


class RandomNumberGenerator:
    def __init__(self, max_num: int, min_num: int):
        self.max_num = max_num
        self.min_num = min_num

    def generate_random_num(self) -> int:
        return randint(self.min_num, self.max_num)


class StatTracker:
    def __init__(self, nums: int):
        self.nums = nums


class MainGame:
    PLAY = "play"
    STATS = "stats"
    QUIT = "quit"

    MAX_NUM = 10
    MIN_NUM = 1

    def __init__(self):
        self.overall_attempts = 0

    def execute(self) -> None:
        choices = [MainGame.PLAY, MainGame.STATS, MainGame.QUIT]
        while True:
            print("List of Choices for the game")
            for i, choice in enumerate(choices):
                print(f"{i + 1}. {choice}")

            choice = input("What is your choice: ").lower().strip()
            if choice == MainGame.PLAY:
                MainGame.play_game()
            elif choice == MainGame.STATS:
                MainGame.display_stats()
            elif choice == MainGame.QUIT:
                break
            else:
                print("Please choose a choice from the list!")
                continue
        print("Thank you for playing this random guess the number game!")

    def play_game(self) -> None:
        generator = RandomNumberGenerator(
            min_num=MainGame.MIN_NUM, 
            max_num=MainGame.MAX_NUM
        )
        correct_num = generator.generate_random_num()
        attempts = 1
        while True:
            try:
                print(f"Attempt #{attempts}")
                player_choice = int(input("Choose a Number: "))
                if player_choice != correct_num:
                    print("Incorrect attempt! Please try again")
                    attempts += 1
                else:
                    print("You have chosen the correct number! Congrats.")
                    print(f"It took you about {attempts} {'attempts' if attempts > 1 else 'attempt'}")
                    self.overall_attempts += attempts
                    break
            except ValueError:
                print("Invalid number, please choose a proper number")

    def display_stats(self) -> None:
        print(f"Overall Stats:")
        print(f"Total Attempts: {self.overall_attempts}")



def main() -> None:
    MainGame().execute()


if __name__ == "__main__":
    main()