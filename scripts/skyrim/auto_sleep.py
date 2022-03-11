import asyncio
import pydirectinput
import keyboard
import pyttsx3
from colored import fg

tts = pyttsx3.init("sapi5")
voices = tts.getProperty("voices")
tts.setProperty("voice", voices[0].id)

sleep_switch = False
sleeping = False


def print_controls():
    cyan, red, green, yellow = fg("light_cyan"), fg(
        "light_red"), fg("light_green"), fg("light_yellow")
    lines = [{"content": "Script Controls:", "color": cyan},
             {"content": "V -> To turn on auto-sleep", "color": green},
             {"content": "B -> To turn off auto-sleep", "color": yellow},
             {"content": "N -> To terminate script", "color": red}]
    for line in lines:
        print(line["color"] + line["content"])


async def text_to_speech(content):
    tts.say(content)
    tts.runAndWait()


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
    asyncio.create_task(text_to_speech("Script is running!"))

    while True:
        if keyboard.is_pressed("v"):
            sleep_switch = True
            await text_to_speech("Auto-sleep on")
        elif keyboard.is_pressed("b"):
            sleep_switch = False
            await text_to_speech("Auto-sleep off")
        elif keyboard.is_pressed("n"):
            await text_to_speech("Script has been terminated")
            break

        if sleep_switch and not sleeping:
            asyncio.create_task(sleep_in_bed())
        await asyncio.sleep(0.025)


if __name__ == "__main__":
    print_controls()
    asyncio.run(main())

# -----------------------------------------------------------------------
# positions = {"sleep": (679, 363), "enter": (539, 424)}
# for position in tuple([x for x in positions]):
#     pydirectinput.doubleClick(*positions[position])
#     await asyncio.sleep(0.25)
# commented this out because pydirectinput clicks doesn't work in-game
