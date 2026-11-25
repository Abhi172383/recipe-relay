"""Page Object for the Recipe List and Search workspace."""

from selenium.webdriver.common.by import By
from .base_page import BasePage


class RecipeListPage(BasePage):
    """Encapsulates recipe search, dietary filtering, and recipe navigation."""

    SEARCH_QUERY = (By.CSS_SELECTOR, "[data-testid='search-query-input']")
    SEARCH_INGREDIENT = (By.CSS_SELECTOR, "[data-testid='search-ingredient-input']")
    SEARCH_SUBMIT = (By.CSS_SELECTOR, "[data-testid='search-submit-btn']")
    NEW_RECIPE_BTN = (By.CSS_SELECTOR, "[data-testid='new-recipe-btn']")

    def search_by_query(self, query: str):
        self.type_text(self.SEARCH_QUERY, query)
        self.click(self.SEARCH_SUBMIT)

    def search_by_ingredient(self, ingredient: str):
        self.type_text(self.SEARCH_INGREDIENT, ingredient)
        self.click(self.SEARCH_SUBMIT)

    def click_new_recipe(self):
        self.click(self.NEW_RECIPE_BTN)

    def open_recipe_by_token(self, share_token: str):
        self.click((By.CSS_SELECTOR, f"[data-testid='open-recipe-{share_token}']"))
