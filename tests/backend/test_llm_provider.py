"""Unit tests for configurable LLM provider adapter and fallback behavior."""

from unittest.mock import MagicMock, patch
import pytest
from recipes.llm_provider import build_user_prompt, generate_substitution_candidates


@pytest.mark.django_db
def test_mock_provider_returns_candidates_when_no_key(settings, seeded_db):
    settings.LLM_PROVIDER = "mock"
    settings.LLM_API_KEY = ""
    candidates, provider = generate_substitution_candidates("butter", "Garlic Pasta", ["dairy"], ["vegan"])
    assert provider == "mock"
    assert len(candidates) >= 1


@pytest.mark.django_db
def test_openai_provider_parses_json_response(settings, seeded_db):
    settings.LLM_PROVIDER = "openai"
    settings.LLM_API_KEY = "fake-test-key"
    settings.LLM_MODEL = "gpt-4o-mini"

    mock_resp = MagicMock()
    mock_payload = (
        '{"candidates": [{"name": "olive oil", '
        '"ratio": "3/4 tbsp", "rationale": "Dairy-free fat."}]}'
    )
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": mock_payload}}]
    }
    mock_resp.raise_for_status.return_value = None

    with patch("recipes.llm_provider.requests.post", return_value=mock_resp) as mock_post:
        candidates, provider = generate_substitution_candidates("butter", "Pasta", ["dairy"], [])
        assert provider == "openai"
        assert candidates[0]["name"] == "olive oil"
        assert mock_post.called


@pytest.mark.django_db
def test_gemini_provider_parses_fenced_json_and_falls_back_on_error(settings, seeded_db):
    settings.LLM_PROVIDER = "gemini"
    settings.LLM_API_KEY = "fake-gemini-key"
    settings.LLM_MODEL = "gemini-2.0-flash"

    mock_resp = MagicMock()
    fenced_payload = (
        '```json\n{"candidates": [{"name": "oat milk", '
        '"ratio": "1:1", "rationale": "Creamy plant milk."}]}\n```'
    )
    mock_resp.json.return_value = {
        "candidates": [
            {"content": {"parts": [{"text": fenced_payload}]}}
        ]
    }
    mock_resp.raise_for_status.return_value = None

    with patch("recipes.llm_provider.requests.post", return_value=mock_resp):
        candidates, provider = generate_substitution_candidates("whole milk")
        assert provider == "gemini"
        assert candidates[0]["name"] == "oat milk"

    # Simulate timeout/network exception -> safe mock-fallback
    with patch("recipes.llm_provider.requests.post", side_effect=RuntimeError("timeout")):
        candidates, provider = generate_substitution_candidates("whole milk")
        assert provider == "mock-fallback"
        assert len(candidates) >= 1


def test_build_user_prompt_includes_constraints():
    prompt = build_user_prompt("butter", "Brioche", ["dairy"], ["vegan"])
    assert "butter" in prompt
    assert "Brioche" in prompt
    assert "dairy" in prompt
    assert "vegan" in prompt
