import pyautogui
import keyboard
import asyncio

sleep_switch = False
sleeping = False


async def sleep_in_bed():
    global sleeping
    sleeping = True
    positions = {"sleep": (), "enter": ()}

    pyautogui.press("e")
    for position in tuple([x for x in positions]):
        pyautogui.click(positions[position])
        await asyncio.sleep(0.25)

    await asyncio.sleep(25)
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
