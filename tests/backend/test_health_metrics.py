"""Tests for health, metrics, preferences, and deterministic rules endpoints."""

import pytest


@pytest.mark.django_db
def test_health_and_metrics_endpoints(api_client, seeded_db):
    health_res = api_client.get("/api/health/")
    assert health_res.status_code == 200
    health_data = health_res.json()
    assert health_data["status"] == "healthy"
    assert health_data["rules_loaded"] >= 40
    assert health_data["recipes_count"] == 8

    # Trigger one substitution request so metrics are non-zero
    api_client.post(
        "/api/substitutions/suggest/",
        {"ingredient": "butter", "allergies": ["dairy"], "inject_unsafe_candidates": ["ghee"]},
        format="json",
    )

    metrics_res = api_client.get("/api/metrics/")
    assert metrics_res.status_code == 200
    metrics_data = metrics_res.json()
    assert metrics_data["reciperelay_substitution_requests_total"] == 1
    assert metrics_data["reciperelay_rejected_candidates_total"] >= 1

    prom_res = api_client.get("/api/metrics/?output=prometheus")
    assert prom_res.status_code == 200
    assert b"reciperelay_recipes_total 8" in prom_res.content


@pytest.mark.django_db
def test_preferences_and_rules_list_endpoints(api_client, seeded_db):
    get_pref = api_client.get("/api/preferences/?profile_key=chef1")
    assert get_pref.status_code == 200
    assert get_pref.json()["allergies"] == []

    put_pref = api_client.put(
        "/api/preferences/",
        {"profile_key": "chef1", "allergies": ["Peanut", "Dairy"], "dietary_preferences": ["Vegan"]},
        format="json",
    )
    assert put_pref.status_code == 200
    assert put_pref.json()["allergies"] == ["peanut", "dairy"]
    assert put_pref.json()["dietary_preferences"] == ["vegan"]

    rules_res = api_client.get("/api/rules/")
    assert rules_res.status_code == 200
    assert len(rules_res.json()) >= 40
