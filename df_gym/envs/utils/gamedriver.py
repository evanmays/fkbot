from selenium import webdriver
import time
from selenium.webdriver.common.keys import Keys

class GameDriver():
    def __init__(self, address, privatekey):
        with open("code.js", "r") as text_file:
            self.js = text_file.read()
        driver = webdriver.Chrome('df_gym/envs/utils/chromedriver')
        self.driver = driver
        driver.get("http://localhost:8081/game1")
        assert "Dark Forest" in driver.title

        time.sleep(2)
        textbox = driver.find_element_by_css_selector("textarea[class^='InputTextArea']")

        def typetext(k, length=0.5):
            textbox.send_keys(k)
            textbox.send_keys(Keys.RETURN)
            time.sleep(length)
        typetext("i")
        typetext(
            privatekey,
            length=3
        )
        time.sleep(5)

        self._callJsFunc(f"disablePopups('{address}')")
        if "Press ENTER to find a home planet" in driver.page_source:
            textbox.send_keys(Keys.RETURN)
            time.sleep(3)

        # start game
        textbox.send_keys(Keys.RETURN)
        time.sleep(5)
        self._callJsFunc("stopExplore()")
        time.sleep(5)
        assert "No results found." not in driver.page_source

    def _callJsFunc(self, function_name):
        return self.driver.execute_script(self.js + "\n" + function_name)

    def move(self):
        self._callJsFunc("randomove()")

    def sendEnergy(self, from_planet_id, to_planet_id, percent_amount):
        self._callJsFunc(f"sendEnergy('{from_planet_id}', '{to_planet_id}', {percent_amount})")

    def getPlanetCount(self):
        return self._callJsFunc("return df.getMyPlanets().length")

    def getAllReachablePlanets(self):
        return self._callJsFunc("return getAllReachablePlanets()")

    def getEnergyScore(self):
        return self._callJsFunc("return df.getEnergyOfPlayer(df.account)")

    def close(self):
        self.driver.close()

    def screenshot(self):
        return self.driver.get_screenshot_as_png()
