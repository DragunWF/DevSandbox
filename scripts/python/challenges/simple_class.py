class Student:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def greet(self) -> str:
        return f"Hello, my name is {self.name} and I am {self.age} year(s) old."


john = Student("John", 20)
alice = Student("Alice", 22)
print(john.greet())
print(alice.greet())
