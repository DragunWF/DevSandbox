# The Pragmatic Programmer 20th Anniversary Edition - Page 146

# In the FSM section we mentioned that you could move the generic state
# machine implementation into its own class. That class would probably be
# initialized by passing in a table of transitions and an initial stae

# Try implementing the stirng extractor that way

# Note: Just the base structure of a FiniteStateMachine

class Transition:
    def __init__(self, header: str, data: str, trailer: str):
        self.initial = {"header": header}
        self.reading = {"data": data, "trailer": trailer}

    def __str__(self) -> str:
        return str({
            "initial": self.initial,
            "reading": self.reading
        })


class FiniteStateMachine:
    def __init__(self, initial: str, transition: Transition):
        self.state = initial
        self.transition = transition

    def __str__(self) -> str:
        return str({
            "state": self.state,
            "transition": str(self.transition)
        })


class Program:
    @staticmethod
    def main() -> None:
        print(FiniteStateMachine("Idle", Transition(
            "Reading Message", "Hello there!", "Done")))


if __name__ == "__main__":
    Program.main()
