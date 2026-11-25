# Prompt Templates — RecipeRelay

This document defines the exact prompt templates used by `src/backend/recipes/llm_provider.py` when calling an external LLM provider (`openai`, `gemini`, or `openai_compatible`), alongside the fallback `mock` mode behavior.

---

## 1. System Prompt Template

```text
You are a culinary assistant suggesting ingredient substitutions.
Return strictly valid JSON with a top-level key 'candidates' containing a list of
objects with keys: name (string), ratio (string), rationale (short string under 25 words).
Do not give medical advice.
```

## 2. User Prompt Template

```text
Suggest up to 4 practical cooking substitutes for '{ingredient}' in recipe '{recipe_title}'.
User allergies to avoid: {allergies_csv}.
Dietary preferences: {dietary_preferences_csv}.
Respond ONLY with JSON: {"candidates": [{"name": "...", "ratio": "...", "rationale": "..."}]}
```

## 3. Why Prompts Alone Are Not Trusted (Defense-in-Depth)
Even though the user prompt explicitly mentions allergies and dietary preferences, LLMs can:
1. Overlook hidden allergen derivatives (e.g., suggesting *ghee* or *whey* for a *dairy*-allergic user, or *tamari* for *soy* allergy).
2. Fail to normalize regional aliases (*groundnut oil* = *peanut oil*, *scallions* = *green onion*).
3. Hallucinate non-existent or unverified blends for unknown ingredients.

Therefore, **every** JSON candidate returned by the LLM is treated as **untrusted input** and gated through `DeterministicRuleValidator` (`src/backend/recipes/rules_engine.py`) backed by the PostgreSQL `IngredientRule` table before anything reaches the user.
