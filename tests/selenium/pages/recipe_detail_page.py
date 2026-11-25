"""Page Object for Recipe Detail, Sharing, and AI Substitution Panel."""

from selenium.webdriver.common.by import By
from .base_page import BasePage


class RecipeDetailPage(BasePage):
    """Encapsulates recipe details, share copy, and substitution validation UI."""

    DETAIL_TITLE = (By.CSS_SELECTOR, "[data-testid='detail-title']")
    COPY_SHARE_BTN = (By.CSS_SELECTOR, "[data-testid='copy-share-btn']")
    SHARE_BANNER = (By.CSS_SELECTOR, "[data-testid='share-copied-banner']")
    SUB_PANEL = (By.CSS_SELECTOR, "[data-testid='substitution-panel']")
    AI_BADGE = (By.CSS_SELECTOR, "[data-testid='ai-assisted-badge']")
    VERIFIED_BADGE = (By.CSS_SELECTOR, "[data-testid='rule-verified-badge']")
    SUGGESTIONS_LIST = (By.CSS_SELECTOR, "[data-testid='suggestions-list']")
    LIMITATIONS = (By.CSS_SELECTOR, "[data-testid='limitations-disclaimer']")

    def get_title(self) -> str:
        return self.find_visible(self.DETAIL_TITLE).text

    def copy_share_link(self) -> str:
        self.click(self.COPY_SHARE_BTN)
        return self.find_visible(self.SHARE_BANNER).text

    def request_substitution(self, ingredient_name: str):
        slug = ingredient_name.lower().replace(" ", "-")
        self.click((By.CSS_SELECTOR, f"[data-testid='suggest-btn-{slug}']"))
        self.find_visible(self.SUB_PANEL)

    def get_ai_badge_text(self) -> str:
        return self.find_visible(self.AI_BADGE).text

    def get_verified_badge_text(self) -> str:
        return self.find_visible(self.VERIFIED_BADGE).text

    def get_suggestions_text(self) -> str:
        return self.find_visible(self.SUGGESTIONS_LIST).text

    def get_limitations_text(self) -> str:
        return self.find_visible(self.LIMITATIONS).text
