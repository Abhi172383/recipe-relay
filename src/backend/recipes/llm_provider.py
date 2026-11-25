"""Configurable LLM provider adapter for generating candidate substitutions.

Supports:
- mock: Deterministic/offline candidate generator (safe default when no API key is set)
- openai / openai_compatible: Chat Completions JSON mode via requests
- gemini: Google Gemini generateContent REST API via requests

On any network/API/parsing failure, falls back cleanly without crashing.
"""

import json
import logging
from typing import List, Optional, Tuple
import requests
from django.conf import settings
from .models import IngredientRule, normalize_ingredient_name

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a culinary assistant suggesting ingredient substitutions. "
    "Return strictly valid JSON with a top-level key 'candidates' containing a list of "
    "objects with keys: name (string), ratio (string), rationale (short string under 25 words). "
    "Do not give medical advice."
)


def build_user_prompt(
    ingredient: str,
    recipe_title: str = "",
    allergies: Optional[List[str]] = None,
    dietary_preferences: Optional[List[str]] = None,
) -> str:
    """Build the substitution prompt template sent to the configured LLM."""
    allergies_str = ", ".join(allergies or []) or "none"
    diets_str = ", ".join(dietary_preferences or []) or "none"
    context = f" in recipe '{recipe_title}'" if recipe_title else ""
    return (
        f"Suggest up to 4 practical cooking substitutes for '{ingredient}'{context}.\n"
        f"User allergies to avoid: {allergies_str}.\n"
        f"Dietary preferences: {diets_str}.\n"
        "Respond ONLY with JSON: {\"candidates\": [{\"name\": \"...\", \"ratio\": \"...\", \"rationale\": \"...\"}]}"
    )


def _mock_candidates(
    ingredient: str,
    inject_unsafe_candidates: Optional[List[str]] = None,
) -> List[dict]:
    """Generate realistic candidate proposals from rule metadata + optional test injections.

    Note: Intentionally returns ALL listed substitutes (including those that may
    conflict with allergies) plus any `inject_unsafe_candidates` so the
    DeterministicRuleValidator proves it filters unsafe LLM proposals.
    """
    norm = normalize_ingredient_name(ingredient)
    rule = IngredientRule.objects.filter(canonical_name=norm).first()
    if rule is None:
        for candidate_rule in IngredientRule.objects.all():
            aliases = [normalize_ingredient_name(a) for a in (candidate_rule.aliases or [])]
            if norm in aliases:
                rule = candidate_rule
                break

    proposals: List[dict] = []
    if rule and rule.allowed_substitutes:
        for sub in rule.allowed_substitutes:
            proposals.append(
                {
                    "name": sub["name"],
                    "ratio": sub.get("ratio", "1:1"),
                    "rationale": sub.get("rationale", "Culinary texture and flavor match."),
                }
            )
    else:
        proposals.append(
            {
                "name": f"unverified substitute for {ingredient}",
                "ratio": "1:1",
                "rationale": "Simulated LLM guess for an unknown or ambiguous ingredient.",
            }
        )

    for unsafe_name in inject_unsafe_candidates or []:
        if not any(normalize_ingredient_name(p["name"]) == normalize_ingredient_name(unsafe_name) for p in proposals):
            proposals.insert(
                0,
                {
                    "name": unsafe_name,
                    "ratio": "1:1",
                    "rationale": "Simulated unsafe LLM candidate requiring deterministic filtering.",
                },
            )
    return proposals


def _parse_llm_json(raw_text: str) -> List[dict]:
    """Extract candidate list from JSON text safely."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
    payload = json.loads(cleaned)
    candidates = payload.get("candidates", [])
    if not isinstance(candidates, list):
        return []
    return [c for c in candidates if isinstance(c, dict) and c.get("name")]


def generate_substitution_candidates(
    ingredient: str,
    recipe_title: str = "",
    allergies: Optional[List[str]] = None,
    dietary_preferences: Optional[List[str]] = None,
    inject_unsafe_candidates: Optional[List[str]] = None,
) -> Tuple[List[dict], str]:
    """Call configured LLM provider or fall back to safe mock mode.

    Returns (candidates_list, provider_used).
    """
    provider = getattr(settings, "LLM_PROVIDER", "mock").lower()
    api_key = getattr(settings, "LLM_API_KEY", "")
    model = getattr(settings, "LLM_MODEL", "gpt-4o-mini")
    timeout = getattr(settings, "LLM_TIMEOUT_SECONDS", 10)

    if provider == "mock" or not api_key:
        return _mock_candidates(ingredient, inject_unsafe_candidates), "mock"

    prompt = build_user_prompt(ingredient, recipe_title, allergies, dietary_preferences)

    try:
        if provider in ("openai", "openai_compatible"):
            base_url = getattr(settings, "LLM_BASE_URL", "") or "https://api.openai.com/v1"
            resp = requests.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return _parse_llm_json(content), provider

        if provider == "gemini":
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model}:generateContent?key={api_key}"
            )
            resp = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": f"{SYSTEM_PROMPT}\n\n{prompt}"}]}],
                    "generationConfig": {"temperature": 0.2},
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            content = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            return _parse_llm_json(content), "gemini"

    except Exception as exc:
        logger.warning("LLM provider '%s' failed (%s); falling back to mock.", provider, exc)
        return _mock_candidates(ingredient, inject_unsafe_candidates), "mock-fallback"

    return _mock_candidates(ingredient, inject_unsafe_candidates), "mock-fallback"
