# The Pragmatic Programmer 20th Anniversary Edition - Page 65

# In the previous exercise we implemented a parser for the drawing language
# it was an external domain language. Now implement it again as an internal
# language. Don't do anything clever: just write a function for each of the
# commands. You may have to change the names of the commands to lower
# case and maybe to wrap them inside something to provide some context

# Output should be
# P 2 - select pen 2
# D - pen down
# W 2 - draw west 2cm
# N 1 - then north
# E 2 - then east 2
# S 1 - then south
# U - pen up

class Turtle:
    __is_last_command_draw = False

    @staticmethod
    def select_pen(pen_num: int) -> None:
        if type(pen_num) != int:
            raise ValueError("Pen selection should be an integer!")
        print(f"select pen {pen_num}")
        Turtle.__is_last_command_draw = False

    @staticmethod
    def pen_down() -> None:
        print("pen down")
        Turtle.__is_last_command_draw = False

    @staticmethod
    def pen_up() -> None:
        print("pen up")
        Turtle.__is_last_command_draw = False

    @staticmethod
    def draw_west(distance: int) -> None:
        Turtle.__draw("west", distance)

    @staticmethod
    def draw_east(distance: int) -> None:
        Turtle.__draw("east", distance)

    @staticmethod
    def draw_north(distance: int) -> None:
        Turtle.__draw("north", distance)

    @staticmethod
    def draw_south(distance: int) -> None:
        Turtle.__draw("south", distance)

    @staticmethod
    def __draw(direction: str, distance: int) -> None:
        if type(distance) != int:
            raise ValueError("Distance for drawing should be an integer!")
        first_word = "draw" if not Turtle.__is_last_command_draw else "then"
        print(f"{first_word} {direction} {distance}")
        Turtle.__is_last_command_draw = True


class Program:
    @staticmethod
    def main() -> None:
        Turtle.select_pen(2)
        Turtle.pen_down()
        Turtle.draw_west(2)
        Turtle.draw_north(1)
        Turtle.draw_east(2)
        Turtle.draw_south(1)
        Turtle.pen_up()


if __name__ == "__main__":
    Program.main()
