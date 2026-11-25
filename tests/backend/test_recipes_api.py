"""Risk-prioritized P1/P2 tests for Recipe CRUD, Sharing, and Search API."""

import pytest


@pytest.mark.django_db
def test_list_and_search_recipes_by_title_and_ingredient(api_client, seeded_db):
    # List all seeded synthetic recipes
    res = api_client.get("/api/recipes/")
    assert res.status_code == 200
    assert len(res.json()) == 8

    # Search by title
    res_title = api_client.get("/api/recipes/?q=Pancakes")
    assert res_title.status_code == 200
    titles = [r["title"] for r in res_title.json()]
    assert "Honey Oat Breakfast Pancakes" in titles
    assert "Creamy Garlic Herb Pasta" not in titles

    # Search by ingredient alias ('chickpea' matches 'garbanzo beans')
    res_ing = api_client.get("/api/recipes/?ingredient=chickpea")
    assert res_ing.status_code == 200
    ing_titles = [r["title"] for r in res_ing.json()]
    assert "Roasted Chickpea & Aubergine Curry" in ing_titles
    assert "Homestyle Vegetable & Bean Soup" in ing_titles

    # Filter by dietary tag
    res_diet = api_client.get("/api/recipes/?diet=vegan")
    assert res_diet.status_code == 200
    assert all("vegan" in r["dietary_tags"] for r in res_diet.json())


@pytest.mark.django_db
def test_recipe_crud_and_share_link_flow(api_client, seeded_db):
    payload = {
        "title": "Test Berry Smoothie Bowl",
        "author_name": "Tester Bot (Synthetic)",
        "description": "Quick dairy-free breakfast bowl.",
        "instructions": "Blend ingredients and top with seeds.",
        "prep_time_minutes": 10,
        "servings": 1,
        "dietary_tags": ["Vegan", "Gluten-Free"],
        "is_public": True,
        "ingredients": [
            {"name": "whole milk", "quantity": "1", "unit": "cup", "notes": ""},
            {"name": "honey", "quantity": "1", "unit": "tbsp", "notes": ""},
        ],
    }

    # Create
    create_res = api_client.post("/api/recipes/", payload, format="json")
    assert create_res.status_code == 201
    created = create_res.json()
    recipe_id = created["id"]
    share_token = created["share_token"]
    assert created["dietary_tags"] == ["vegan", "gluten-free"]
    assert len(created["ingredients"]) == 2

    # Share lookup
    share_res = api_client.get(f"/api/recipes/share/{share_token}/")
    assert share_res.status_code == 200
    assert share_res.json()["id"] == recipe_id

    # Update
    update_res = api_client.patch(
        f"/api/recipes/{recipe_id}/",
        {
            "title": "Updated Berry Smoothie Bowl",
            "ingredients": [{"name": "oat milk", "quantity": "1", "unit": "cup"}],
        },
        format="json",
    )
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Updated Berry Smoothie Bowl"
    assert update_res.json()["ingredients"][0]["name"] == "oat milk"

    # Delete
    del_res = api_client.delete(f"/api/recipes/{recipe_id}/")
    assert del_res.status_code == 204
    assert api_client.get(f"/api/recipes/{recipe_id}/").status_code == 404


@pytest.mark.django_db
def test_recipe_validation_requires_ingredients(api_client):
    res = api_client.post(
        "/api/recipes/",
        {
            "title": "Empty Recipe",
            "instructions": "Nothing here",
            "ingredients": [],
        },
        format="json",
    )
    assert res.status_code == 400
    assert "ingredients" in res.json()
