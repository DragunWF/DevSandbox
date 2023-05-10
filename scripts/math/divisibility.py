# This just serves as one of my practice programs for number theory
# in my Discrete Mathematics subject.

import random
from rich import print
from colored import fg


class DivisibilityGame:
    def __init__(self, questions: int):
        if questions <= 0:
            raise Exception('"numbers" argument must be a positive integer!')
        self.__chosen_numbers = []
        self.__questions = questions
        self.__divisor_range = (2, 12)
        self.__range = (10, 5000)

    def __generate_numbers(self) -> None:
        for i in range(self.__questions):
            random_num = random.randint(self.__range[0], self.__range[1])
            if not random_num in self.__chosen_numbers:
                self.__chosen_numbers.append(random_num)

    def __generate_table(self) -> list:
        table = [self.__generate_header()]
        for number in self.__chosen_numbers:
            table.append(self.__generate_row(number))
        return table

    def __digits_len(self, number: int) -> int:
        return len(str(number))

    def __generate_header(self) -> str:
        output = [f"{self.__range[1] * ' '}   "]
        for i in range(self.__divisor_range[0], self.__divisor_range[1] + 1):
            output.append(str(i))
        return " | ".join(output)

    def __generate_row(self, number: int) -> list:
        output = []
        whitespaces = self.__digits_len(
            self.__range[1]) - self.__digits_len(number)
        output.append(f"{number}{(whitespaces + 1) * ' '}")
        for i in range(self.__divisor_range[0], self.__divisor_range[1] + 1):
            cell = "Y" if number % i == 0 else "N"
            output.append(f"{cell}{(self.__digits_len(i) - 1) * ' '}")
        return " | ".join(output)

    def play(self) -> None:
        self.__generate_numbers()
        table = self.__generate_table()
        for row in table:
            print(row)


if __name__ == "__main__":
    DivisibilityGame(100).play()
