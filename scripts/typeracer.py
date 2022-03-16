import time
from colored import fg
from pynput.keyboard import Controller
from webdriver_manager.chrome import ChromeDriverManager

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

path = r"C:\webdrivers\chromedriver.exe"
driver = webdriver.Chrome(ChromeDriverManager().install())

keyboard = Controller()


def main():
    driver.get("https://play.typeracer.com/")

    try:
        start_game = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.LINK_TEXT, "Enter a Typing Race"))
        )
        start_game.click()
        time.sleep(0.3)

        for i in range(10):
            print(fg("light_green") + f"Iteration: {i + 1}")

            input_panel = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "inputPanel"))
            )
            text = input_panel.text.split("\n")[0]

            while True:
                game_time = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "lightLabel"))
                )
                print(game_time.text)
                if game_time.text == "Go!":
                    break
                time.sleep(0.2)

            for chr in text:
                keyboard.type(chr)
                time.sleep(0.085)
            time.sleep(0.1)

            new_game = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.LINK_TEXT, "Enter a Typing Race"))
            )
            new_game.click()
            time.sleep(0.1)

    except:
        driver.quit()


if __name__ == "__main__":
    main()
