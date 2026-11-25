"""Shared pytest fixtures for RecipeRelay backend tests."""

import os
import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

os.environ.setdefault("USE_SQLITE", "true")


@pytest.fixture
def api_client():
    """Return an unauthenticated DRF APIClient."""
    return APIClient()


@pytest.fixture
def seeded_db(db):
    """Populate deterministic IngredientRule and synthetic Recipe fixtures."""
    call_command("seed_data")
    return True
