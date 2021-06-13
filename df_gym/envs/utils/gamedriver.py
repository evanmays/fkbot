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

        time.sleep(4)
        textbox = driver.find_element_by_css_selector("textarea[class^='InputTextArea']")
        assert textbox
        time.sleep(2)
        def typetext(k, length=0.5):
            textbox.send_keys(k)
            textbox.send_keys(Keys.RETURN)
            time.sleep(length)
        typetext("i")
        self._waitToSee("Enter the 0x-prefixed private key")
        assert "Enter the 0x-prefixed private key" in driver.page_source
        typetext(
            privatekey,
            length=3
        )
        time.sleep(5)
        assert "Press ENTER to find a home planet" in driver.page_source

        self._callJsFunc(f"disablePopups('{address}')")
        time.sleep(1)
        textbox.send_keys(Keys.RETURN)
        time.sleep(3)

        # start game
        textbox.send_keys(Keys.RETURN)
        time.sleep(5)
        self._callJsFunc("stopExplore()")
        time.sleep(5)
        loading_complete = False
        while not loading_complete:
            time.sleep(1)
            loading_complete = self.getPlanetCount() > 0
        assert "No results found." not in driver.page_source

    def _waitToSee(self, text):
        start = time.time()
        can_see = False
        while not can_see:
            time.sleep(1)
            can_see = text in self.driver.page_source
            if time.time() - start > 10:
                assert False, f"10 seconds has passed and we didn't see '{text}'"
    def _callJsFunc(self, function_name):
        return self.driver.execute_script(self.js + "\n" + function_name)

    def move(self):
        self._callJsFunc("randomove()")

    def sendEnergy(self, from_planet_id, to_planet_id, percent_amount):
        print(f"sendEnergy('{from_planet_id}', '{to_planet_id}', {percent_amount})")
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
