"""Base Page Object with explicit WebDriver waits."""

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BasePage:
    """Base helper for RecipeRelay Selenium Page Objects."""

    def __init__(self, driver, base_url: str, timeout: int = 10):
        self.driver = driver
        self.base_url = base_url.rstrip("/")
        self.wait = WebDriverWait(driver, timeout)

    def open(self, path: str = "/"):
        self.driver.get(f"{self.base_url}{path}")

    def find_visible(self, locator):
        return self.wait.until(EC.visibility_of_element_located(locator))

    def click(self, locator):
        elem = self.wait.until(EC.element_to_be_clickable(locator))
        elem.click()
        return elem

    def type_text(self, locator, text: str):
        elem = self.find_visible(locator)
        elem.clear()
        elem.send_keys(text)
        return elem
