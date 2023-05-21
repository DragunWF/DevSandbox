# Not Finished

import random
from rich import print


class MathGame:
    def __init__(self, problems: int):
        self.__chosen_numbers = []
        self.__RANGE = (15, 1000)
        for i in range(problems):
            random_num = random.randint(self.__RANGE[0],self.__RANGE[1])
            if not random_num in self.__chosen_numbers:
                self.__chosen_numbers.append(random_num)

    def play() -> None:
        pass


if __name__ == "__main__":
    MathGame().play(0)
