"""P0 Safety-Critical tests for deterministic ingredient rules and substitution API."""

import pytest
from recipes.rules_engine import DeterministicRuleValidator


@pytest.mark.django_db
def test_rejects_dairy_candidates_and_returns_safe_alternatives(api_client, seeded_db):
    res = api_client.post(
        "/api/substitutions/suggest/",
        {
            "ingredient": "butter",
            "allergies": ["dairy"],
            "dietary_preferences": [],
            "inject_unsafe_candidates": ["ghee"],
        },
        format="json",
    )
    assert res.status_code == 200
    data = res.json()
    assert data["ai_assisted"] is True
    assert data["status"] == "verified"
    assert "limitations" in data and "cross-contamination" in data["limitations"].lower()

    suggested_names = [s["name"] for s in data["suggestions"]]
    assert "ghee" not in suggested_names
    assert "olive oil" in suggested_names
    rejected_names = [r["name"] for r in data["rejected_candidates"]]
    assert "ghee" in rejected_names


@pytest.mark.django_db
def test_handles_aliases_and_hidden_allergens(api_client, seeded_db):
    # 'casein' resolves to whey protein (dairy allergen) -> pea protein
    res = api_client.post(
        "/api/substitutions/suggest/",
        {"ingredient": "casein", "allergies": ["dairy"], "dietary_preferences": []},
        format="json",
    )
    assert res.status_code == 200
    data = res.json()
    assert data["resolved_canonical"] == "whey protein"
    assert data["suggestions"][0]["name"] == "pea protein"

    # 'groundnut oil' resolves to peanut oil -> rejects peanut, keeps sunflower/canola
    res_peanut = api_client.post(
        "/api/substitutions/suggest/",
        {"ingredient": "groundnut oil", "allergies": ["peanut"], "dietary_preferences": []},
        format="json",
    )
    assert res_peanut.status_code == 200
    assert res_peanut.json()["resolved_canonical"] == "peanut oil"
    assert len(res_peanut.json()["suggestions"]) >= 1


@pytest.mark.django_db
def test_rejects_unapproved_llm_candidate_even_without_allergy(seeded_db):
    validator = DeterministicRuleValidator()
    outcome = validator.validate(
        ingredient_name="butter",
        candidates=[
            {"name": "mystery industrial fat", "ratio": "1:1", "rationale": "AI guess"},
            {"name": "olive oil", "ratio": "3/4 tbsp", "rationale": "Healthy fat"},
        ],
        allergies=[],
        dietary_preferences=[],
    )
    assert outcome.status == "verified"
    assert [s["name"] for s in outcome.accepted] == ["olive oil"]
    assert outcome.rejected[0]["name"] == "mystery industrial fat"


@pytest.mark.django_db
def test_ambiguous_and_missing_ingredients_return_safe_no_suggestion(api_client, seeded_db):
    # Ambiguous ingredient 'flour'
    res_ambig = api_client.post(
        "/api/substitutions/suggest/",
        {"ingredient": "flour", "allergies": ["gluten"], "inject_unsafe_candidates": ["wheat flour"]},
        format="json",
    )
    assert res_ambig.status_code == 200
    assert res_ambig.json()["status"] == "no_safe_suggestion"
    assert res_ambig.json()["suggestions"] == []

    # Missing ingredient 'dragonfruit powder'
    res_missing = api_client.post(
        "/api/substitutions/suggest/",
        {"ingredient": "dragonfruit powder", "allergies": ["dairy"]},
        format="json",
    )
    assert res_missing.status_code == 200
    assert res_missing.json()["status"] == "no_safe_suggestion"
    assert res_missing.json()["suggestions"] == []


@pytest.mark.django_db
def test_substitution_uses_saved_dietary_profile_by_default(api_client, seeded_db):
    put_res = api_client.put(
        "/api/preferences/",
        {
            "profile_key": "default",
            "allergies": ["dairy", "tree_nut"],
            "dietary_preferences": ["vegan"],
        },
        format="json",
    )
    assert put_res.status_code == 200

    res = api_client.post(
        "/api/substitutions/suggest/",
        {"ingredient": "whole milk", "profile_key": "default"},
        format="json",
    )
    assert res.status_code == 200
    names = [s["name"] for s in res.json()["suggestions"]]
    assert "almond milk" not in names
    assert "oat milk" in names
