import pyautogui
from colored import fg
from time import sleep

green = fg("light_green")
red = fg("light_red")
cyan = fg("light_cyan")


def execute_clicks():
    positions = {"FirstCrypto": (1310, 20), "SecondCrypto": (1311, 114),
                 "ThirdCrypto": (1312, 203), "FirstIcon": (408, 528),
                 "OtherIcons": (479, 509), "Desktop": (1359, 746)}
    actions = ("Desktop",
               "FirstCrypto", "FirstIcon", "Desktop",
               "SecondCrypto", "OtherIcons", "Desktop",
               "ThirdCrypto", "OtherIcons", "Desktop",)

    for position in actions:
        pyautogui.doubleClick(positions[position])
        sleep(1.5 if position in ("FirstCrypto",
              "SecondCrypto", "ThirdCrypto") else 0.1)


def main():
    try:
        print(cyan + "Executing browser automation...")
        sleep(0.01)
        execute_clicks()
        sleep(0.1)
        print(green + "Script has been executed successfully")
        sleep(5)
    except Exception:
        print(red + "An error has occured")
        sleep(30)


if __name__ == "__main__":
    main()
