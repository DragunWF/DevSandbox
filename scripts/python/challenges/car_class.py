class Car:
    def __init__(self, brand: str, model: str, year: int):
        self.brand = brand
        self.model = model
        self.year = year

    def display_info(self) -> str:
        return f"Brand: {self.brand}\nModel: {self.model}\nYear: {self.year}"


first_car = Car('Toyota', 'Corolla', 2020)
second_car = Car('Honda', 'Civic', 2022)
print(first_car.display_info())
print()
print(second_car.display_info())
