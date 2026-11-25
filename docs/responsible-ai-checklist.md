# Responsible AI Checklist — RecipeRelay

| Principle | Implementation in RecipeRelay | Verification |
|-----------|-------------------------------|--------------|
| **1. Never Trust Raw LLM Output** | `DeterministicRuleValidator` intercepts every candidate from `llm_provider.py` before returning to the UI. | `tests/backend/test_rules_engine.py` + `tests/evaluate_substitutions.py` |
| **2. Allergen & Alias Safety** | Canonical `IngredientRule` table normalizes aliases (`casein`->`whey protein`->`dairy`, `groundnut oil`->`peanut oil`) and checks both source and candidate allergens. | 40-case evaluation suite (100% allergy-safe target) |
| **3. Safe Failure on Ambiguity / Unknowns** | Ambiguous (`flour`, `oil`, `stock`) and unknown (`dragonfruit powder`) ingredients return `status: "no_safe_suggestion"` with zero substitutes. | `test_ambiguous_and_missing_ingredients_return_safe_no_suggestion` |
| **4. Explicit AI Transparency** | UI and API include `ai_assisted: true`, `"AI-Assisted"` badge, provider name, and rejected-candidate transparency list. | `SubstitutionPanel.jsx`, `App.test.jsx`, Selenium journey |
| **5. Appropriate Limitations Notice** | Every substitution result renders a cross-contamination & packaged-label verification disclaimer. | `SubstitutionPanel.jsx` (`data-testid="limitations-disclaimer"`) |
| **6. Privacy & Synthetic-Only Data** | Zero real personal data (PII); all seed recipes and profiles use synthetic aliases (`Chef Aria (Synthetic)`). | `data/seed_recipes.json`, `.env.example` |
| **7. Auditability** | Every substitution check is persisted in `SubstitutionAuditLog` (raw vs. accepted vs. rejected candidates). | `recipes/models.py`, `/api/metrics/` |
