import pyautogui
from time import sleep
from colored import fg

green = fg("light_green")
red = fg("light_red")
cyan = fg("light_cyan")


def execute_clicks():
    positions = {"FirstCrypto": (1310, 20), "SecondCrypto": (1311, 114),
                 "ThirdCrypto": (1312, 203), "FirstIcon": (569, 500),
                 "OtherIcons": (620, 469), "Desktop": (1359, 746)}
    actions = ("FirstCrypto", "FirstIcon", "Desktop",
               "SecondCrypto", "OtherIcons", "Desktop",
               "ThirdCrypto", "OtherIcons", "Desktop")
    for position in actions:
        pyautogui.doubleClick(positions[position])
        sleep(0.1)


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
