# The Pragmatic Programmer 20th Anniversary Edition - Page 64

# We want to implement a mini-language to control a simple turtle-graphics
# system. The language consists of single-letter commands, some followed by
# a single number. For example, the following input would draw a rectangle
# Implement the code that parses this language. It should be designed so
# that it is simple to add new commands.

# Output should be
# P 2 - select pen 2
# D - pen down
# W 2 - draw west 2cm
# N 1 - then north
# E 2 - then east 2
# S 1 - then south
# U - pen up

from abc import ABC, abstractmethod

code = """
P 2
D
W 2
N 1
E 2
S 1
U
"""


class Command(ABC):
    def __init__(self, identifier: str, prompt: str):
        self.identifier = identifier
        self.prompt = prompt

    def get_identifier(self) -> str:
        return self.identifier

    @abstractmethod
    def execute(self) -> None:
        pass


class GenericCommand(Command):
    def __init__(self, identifier: str, prompt: str):
        super().__init__(identifier, prompt)

    def execute(self) -> None:
        print(self.prompt)


class ArgumentCommand(Command):
    def __init__(self, identifier: str, prompt: str):
        super().__init__(identifier, prompt)

    def execute(self) -> None:
        raise Exception(
            "Missing Argument Error: Must specify a number for drawing"
        )

    def execute(self, arg) -> None:
        print(f"{self.prompt} {arg}")


class DrawCommand(Command):
    def __init__(self, command: str, prompt: str, alternate_prompt: str):
        super().__init__(command, prompt)
        self.alternate_prompt = alternate_prompt

    def execute(self) -> None:
        raise Exception(
            "Missing Argument Error: Must specify a number for drawing"
        )

    def execute(self, draw_length: str, is_initial_stroke: bool) -> int:
        if not draw_length.isdigit():
            raise ValueError(
                "Draw length argument for draw command should be a digit!"
            )
        print(
            f"{self.prompt if not is_initial_stroke else self.alternate_prompt} {draw_length}"
        )


class Interpreter:
    def __init__(self, commands: list[Command]):
        self.__commands = {}
        for command in commands:
            self.__commands[command.get_identifier()] = command

        self.last_command_is_draw = False

    def __get_command(self, identifier: str) -> Command:
        return self.__commands[identifier]

    def __execute_command(self, line: str) -> None:
        if not line.strip():
            return

        tokens = line.strip().split(" ")
        command_identifier = tokens[0]
        if command_identifier in self.__commands:
            command = self.__get_command(command_identifier)
            IS_DRAW_COMMAND = type(command) == DrawCommand
            IS_ARGUMENT_COMMAND = type(command) == ArgumentCommand
            IS_GENERIC_COMMAND = type(command) == GenericCommand

            if (IS_DRAW_COMMAND or IS_ARGUMENT_COMMAND) and len(tokens) != 2:
                raise Exception(
                    f"There should be one argument for the command '{command_identifier}'"
                )

            if IS_DRAW_COMMAND:
                command.execute(tokens[1], self.last_command_is_draw)
            elif IS_ARGUMENT_COMMAND:
                command.execute(tokens[1])
            elif IS_GENERIC_COMMAND:
                command.execute()

            self.last_command_is_draw = IS_DRAW_COMMAND
        else:
            raise Exception("Command is not recognized!")

    def interpret(self, code: str):
        lines = code.split("\n")
        for line in lines:
            self.__execute_command(line)


class Program:
    @staticmethod
    def main() -> None:
        Interpreter([
            ArgumentCommand("P", "select pen"),
            GenericCommand("D", "pen down"),
            GenericCommand("U", "pen up"),
            DrawCommand("W", "draw west", "then west"),
            DrawCommand("E", "draw east", "then east"),
            DrawCommand("N", "draw north", "then north"),
            DrawCommand("S", "draw south", "then south")
        ]).interpret(code)


if __name__ == "__main__":
    Program.main()
