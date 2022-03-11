import asyncio
import pydirectinput
import keyboard

sleep_switch = False
sleeping = False


async def sleep_in_bed():
    global sleeping
    sleeping = True

    pydirectinput.press("e")
    await asyncio.sleep(0.5)
    pydirectinput.keyDown("d")
    await asyncio.sleep(3)
    pydirectinput.keyUp("d")
    await asyncio.sleep(0.1)
    pydirectinput.press("enter")

    await asyncio.sleep(30)
    sleeping = False


async def main():
    global sleep_switch
    while True:
        if keyboard.is_pressed("o"):
            sleep_switch = True
        elif keyboard.is_pressed("p"):
            sleep_switch = False
        elif keyboard.is_pressed("l"):
            break

        if sleep_switch and not sleeping:
            asyncio.create_task(sleep_in_bed())
        await asyncio.sleep(0.025)


if __name__ == "__main__":
    asyncio.run(main())

# Dump
# positions = {"sleep": (679, 363), "enter": (539, 424)}
# for position in tuple([x for x in positions]):
#     pydirectinput.doubleClick(*positions[position])
#     await asyncio.sleep(0.25)
# Commented this out because pydirectinput clicks doesn't work in-game
