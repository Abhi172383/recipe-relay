"""End-to-end Selenium browser journey using Page Object Model.

Run against a live frontend + backend:
    SELENIUM_BASE_URL=http://127.0.0.1:5173 .venv/bin/pytest tests/selenium/test_user_journey.py
"""

import os
import sys
from pathlib import Path
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pages.preferences_page import PreferencesPage  # noqa: E402
from pages.recipe_detail_page import RecipeDetailPage  # noqa: E402
from pages.recipe_form_page import RecipeFormPage  # noqa: E402
from pages.recipe_list_page import RecipeListPage  # noqa: E402


@pytest.fixture
def browser():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1366,900")
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()


def test_end_to_end_recipe_and_safe_substitution_journey(browser):
    base_url = os.getenv("SELENIUM_BASE_URL", "http://127.0.0.1:5173")

    list_page = RecipeListPage(browser, base_url)
    prefs_page = PreferencesPage(browser, base_url)
    form_page = RecipeFormPage(browser, base_url)
    detail_page = RecipeDetailPage(browser, base_url)

    # 1. Open app and set Dairy + Tree Nut allergy exclusions
    list_page.open("/")
    prefs_page.set_allergy("dairy", True)
    prefs_page.set_allergy("tree_nut", True)
    prefs_page.save()
    prefs_page.wait_for_summary_contains("dairy")
    assert "dairy" in prefs_page.get_summary_text().lower()

    # 2. Search existing seeded recipe by ingredient alias ('chickpea')
    list_page.search_by_ingredient("chickpea")
    list_page.open_recipe_by_token("chickpea-curry-02")
    assert "Chickpea" in detail_page.get_title()

    # 3. Request dairy-free substitution for greek yogurt and verify AI-assisted + safety notice
    detail_page.request_substitution("greek yogurt")
    assert "AI-Assisted" in detail_page.get_ai_badge_text()
    assert "Deterministic Rule Verified" in detail_page.get_verified_badge_text()
    assert "coconut yogurt" in detail_page.get_suggestions_text().lower()
    assert "cross-contamination" in detail_page.get_limitations_text().lower()

    # 4. Copy share link and verify banner
    banner = detail_page.copy_share_link()
    assert "chickpea-curry-02" in banner

    # 5. Create a new synthetic recipe via UI form and test milk substitution (must exclude almond milk!)
    list_page.click_new_recipe()
    form_page.fill_and_submit(
        title="Selenium Test Oat Porridge",
        description="Automated E2E verification recipe.",
        tags="breakfast, vegetarian",
        ingredients=[{"name": "whole milk", "quantity": "1", "unit": "cup"}],
        instructions="Simmer oats in milk for 5 minutes.",
    )
    assert detail_page.get_title() == "Selenium Test Oat Porridge"
    detail_page.request_substitution("whole milk")
    suggestions_text = detail_page.get_suggestions_text().lower()
    assert "oat milk" in suggestions_text
    assert "almond milk" not in suggestions_text
