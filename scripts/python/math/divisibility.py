# This just serves as one of my practice programs for number theory
# in my Discrete Mathematics subject.

import random
from rich import print


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
        output = [f"{self.__digits_len(self.__range[1]) * ' '} "]
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

    def __prompt_user(self) -> None:
        print("Numbers: ", end="")
        for i in range(len(self.__chosen_numbers)):
            print(self.__chosen_numbers[i],
                  end=" " if (i + 1) % 5 != 0 else "\n")
        input("\nEnter anything to show answers ")
        print()

    def play(self) -> None:
        self.__generate_numbers()
        self.__prompt_user()

        table = self.__generate_table()
        for row in table:
            print(row)


class Utils:
    @staticmethod
    def choose_number() -> int:
        try:
            output = int(
                input("Input the amount of numbers you want to solve with divisibility: "))
        except ValueError:
            return Utils.choose_number()
        return output


if __name__ == "__main__":
    DivisibilityGame(Utils.choose_number()).play()
