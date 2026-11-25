"""Page Object for the Dietary & Allergy Preferences sidebar."""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from .base_page import BasePage


class PreferencesPage(BasePage):
    """Encapsulates allergy and diet preference toggles."""

    SAVE_BTN = (By.CSS_SELECTOR, "[data-testid='save-preferences-btn']")
    PROFILE_SUMMARY = (By.CSS_SELECTOR, "[data-testid='active-profile-summary']")

    def set_allergy(self, allergy_key: str, enabled: bool = True):
        locator = (By.CSS_SELECTOR, f"[data-testid='allergy-{allergy_key}']")
        checkbox = self.find_visible(locator)
        if checkbox.is_selected() != enabled:
            checkbox.click()

    def save(self):
        self.click(self.SAVE_BTN)

    def wait_for_summary_contains(self, text: str):
        self.wait.until(EC.text_to_be_present_in_element(self.PROFILE_SUMMARY, text))

    def get_summary_text(self) -> str:
        return self.find_visible(self.PROFILE_SUMMARY).text
