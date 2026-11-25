"""Page Object for Create/Edit Recipe Form."""

from selenium.webdriver.common.by import By
from .base_page import BasePage


class RecipeFormPage(BasePage):
    """Encapsulates creating a recipe with structured ingredients."""

    TITLE_INPUT = (By.CSS_SELECTOR, "[data-testid='recipe-title-input']")
    DESC_INPUT = (By.CSS_SELECTOR, "[data-testid='recipe-desc-input']")
    TAGS_INPUT = (By.CSS_SELECTOR, "[data-testid='recipe-tags-input']")
    INSTRUCTIONS_INPUT = (By.CSS_SELECTOR, "[data-testid='recipe-instructions-input']")
    ADD_ING_BTN = (By.CSS_SELECTOR, "[data-testid='add-ingredient-btn']")
    SUBMIT_BTN = (By.CSS_SELECTOR, "[data-testid='submit-recipe-btn']")

    def fill_and_submit(self, title: str, description: str, tags: str, ingredients: list, instructions: str):
        self.type_text(self.TITLE_INPUT, title)
        self.type_text(self.DESC_INPUT, description)
        self.type_text(self.TAGS_INPUT, tags)

        for idx, ing in enumerate(ingredients):
            if idx > 0:
                self.click(self.ADD_ING_BTN)
            self.type_text((By.CSS_SELECTOR, f"[data-testid='ingredient-name-{idx}']"), ing["name"])
            self.type_text((By.CSS_SELECTOR, f"[data-testid='ingredient-qty-{idx}']"), ing.get("quantity", "1"))
            self.type_text((By.CSS_SELECTOR, f"[data-testid='ingredient-unit-{idx}']"), ing.get("unit", "cup"))

        self.type_text(self.INSTRUCTIONS_INPUT, instructions)
        self.click(self.SUBMIT_BTN)
