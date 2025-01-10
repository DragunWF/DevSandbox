# Implement Design by Contract (DBC)
# Design an interface to a kitchen blender. It will eventually be a web-based
# IoT-enabled blender, but for now we just need the interface to control it. It
# has ten speed settings (0 means off). You can't operate it empty, and you can
# change the speed only one unit at a time (that is, from 0 to 1), and from 1 to
# 2, not from 0 to 2.

class KitchenBlender:
    __MIN_SPEED = 0
    __MAX_SPEED = 10

    def __init__(self, speed: int):
        self.assert_invariants(speed)
        self.__speed = speed
        self.__is_filled = False

    def assert_invariants(self, speed: int):
        assert KitchenBlender.__MIN_SPEED <= speed <= KitchenBlender.__MAX_SPEED, f"speed must be between {KitchenBlender.__MIN_SPEED} and {KitchenBlender.__MAX_SPEED}."

    def get_speed(self) -> int:
        return self.__speed

    def set_speed(self, speed: int) -> None:
        """
            @precondition: KitchenBlender.__MIN_SPEED <= speed <= KitchenBlender.__MAX_SPEED
            @postcondition: speed == self.__speed + 1 or speed == self.__speed - 1
        """

        # Pre-condition
        self.assert_invariants(speed)

        self.__speed = speed

        # Post-condition
        assert (speed == self.__speed + 1 or speed == self.__speed -
                1), "speed can only be changed one unit at at time"

    def is_full(self) -> bool:
        return self.__is_filled

    def fill(self) -> None:
        self.__is_filled = True

    def empty(self) -> None:
        self.__is_filled = False

    def operate(self) -> None:
        """
            @precondition: KitchenBlender must not be empty
            @postcondition: KitchenBlender is operating
        """
        # Precondition
        assert self.is_full(), "Kitchen blender must not be empty"

        print("Blender is being operated on")


def main() -> None:
    kitchen_blender = KitchenBlender(0)
    kitchen_blender.set_speed(1)
    kitchen_blender.set_speed(2)
    kitchen_blender.set_speed(3)

    # kitchen_blender.set_speed(-1)
    # kitchen_blender.set_speed(1000)

    kitchen_blender.fill()
    kitchen_blender.empty()

    kitchen_blender.operate()


if __name__ == '__main__':
    main()
