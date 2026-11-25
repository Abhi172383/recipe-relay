# Software Requirements Specification (SRS)
## RecipeRelay: Recipe Sharing with Ingredient Substitution

**Course / Handbook:** AI in Software Engineering — P43  
**Project Version:** 1.0.0  
**Data Policy:** Synthetic seed data only; no real personal data (PII) is stored or processed.

---

## 1. Purpose & Scope
RecipeRelay is a full-stack web application for home cooks and food bloggers to create, share, and search recipes while safely discovering AI-assisted ingredient substitutions tailored to dietary preferences and allergy exclusions.

Because Large Language Models (LLMs) can hallucinate unsafe substitutes or miss hidden allergens (e.g., recommending *whey* to a dairy-allergic user or *groundnut oil* to a peanut-allergic user), RecipeRelay enforces a **deterministic ingredient rules table** in PostgreSQL that validates every LLM-generated candidate before display.

---

## 2. System Stakeholders & Personas
1. **Home Cook (Primary User):** Searches recipes by title or pantry ingredients, sets allergy/dietary filters, and requests safe ingredient swaps.
2. **Food Blogger / Contributor:** Creates, edits, deletes, and shares public recipe links with structured ingredient quantities and tags.
3. **QA / Safety Reviewer (Student / Maintainer):** Audits deterministic rule coverage, runs the 40-case substitution evaluation suite, and reviews prompt logs and SonarQube quality gates.

---

## 3. Functional Requirements

| ID | Requirement | Priority | Sprint |
|----|-------------|----------|--------|
| **FR-1** | **Recipe CRUD:** Users can create, read, update, and delete recipes with title, author alias, description, prep time, servings, dietary tags, instructions, and structured ingredients (`name`, `quantity`, `unit`, `notes`). | Must | Sprint 1 |
| **FR-2** | **Recipe Sharing:** Each public recipe generates a unique `share_token` and shareable URL (`/recipes/share/<token>` or `?share=<token>`) with one-click copy-to-clipboard feedback. | Must | Sprint 1 |
| **FR-3** | **Title & Ingredient Search:** Users can search recipes by keyword matching against both recipe `title` and `ingredients.name` (case-insensitive, partial match) and filter by dietary tags. | Must | Sprint 1 |
| **FR-4** | **Dietary Preferences & Allergy Exclusions:** Users can configure and persist active allergies (e.g., `dairy`, `peanut`, `tree_nut`, `gluten`, `egg`, `soy`, `shellfish`, `sesame`) and dietary preferences (`vegan`, `vegetarian`, `dairy-free`, `gluten-free`, `nut-free`). | Must | Sprint 2 |
| **FR-5** | **AI-Assisted Candidate Generation:** A configurable LLM adapter (`mock`, `openai`, `gemini`, `openai_compatible`) proposes candidate ingredient swaps with culinary rationale and conversion ratio. | Must | Sprint 2 |
| **FR-6** | **Deterministic Rule Validation Gate:** Every LLM candidate MUST be checked against the `IngredientRule` table before display. It must resolve ingredient aliases (e.g., `scallions` -> `green onion`, `casein` -> `dairy` allergen), reject known allergen and dietary conflicts, and reject unknown or ambiguous ingredients. | Must | Sprint 2 |
| **FR-7** | **Safe Fallback Response:** If no candidate passes validation, or if the source ingredient rule is missing or flagged ambiguous, the API returns a safe `no_safe_suggestion` response explaining why rather than guessing. | Must | Sprint 2 |
| **FR-8** | **AI Transparency & Limitations UI:** Every substitution panel displays an explicit **AI-assisted** badge, validation status (`Verified Safe` / `No Safe Suggestion`), and a safety limitations notice advising label verification for cross-contamination. | Must | Sprint 2 |
| **FR-9** | **Observability Endpoints:** Expose `GET /api/health/` (DB, rules count, provider mode) and `GET /api/metrics/` (request counts, safety rejection metrics, latency). | Should | Sprint 2 |

---

## 4. Non-Functional Requirements

| ID | Category | Specification | Target |
|----|----------|---------------|--------|
| **NFR-1** | **Safety** | Zero allergen-conflicting substitutions shown across the 40-case evaluation suite. | 100% allergy-safe |
| **NFR-2** | **Reliability** | LLM timeouts or malformed JSON never crash the API; adapter falls back safely or returns `no_safe_suggestion`. | 0 unhandled 500s |
| **NFR-3** | **Testability** | Automated unit/integration test suite with branch/statement coverage reporting. | >= 80% coverage |
| **NFR-4** | **Accessibility** | WCAG 2.1 AA basics: semantic landmarks, form labels, keyboard-reachable controls, live-region status updates, visible focus rings. | Keyboard & screen-reader usable |
| **NFR-5** | **Security** | No secrets committed (`.env.example` only), parameterized ORM queries, CORS allowlisting, synthetic seed data only. | 0 SonarQube blockers |
| **NFR-6** | **Portability** | Reproducible setup via Docker Compose (`db`, `backend`, `frontend`) and local Python/Node workflows. | Single-command boot |

---

## 5. Requirements Traceability Matrix (Summary)
- `FR-1, FR-2, FR-3` -> `recipes/models.py`, `recipes/views.py`, `RecipeList.jsx`, `RecipeForm.jsx`, `RecipeDetail.jsx` -> `tests/backend/test_recipes_api.py`, `tests/selenium/test_user_journey.py`
- `FR-4, FR-5, FR-6, FR-7, FR-8` -> `recipes/rules_engine.py`, `recipes/llm_provider.py`, `SubstitutionPanel.jsx`, `PreferencesPanel.jsx` -> `tests/backend/test_rules_engine.py`, `tests/evaluate_substitutions.py`
- `FR-9` -> `recipes/views.py` (`health_check`, `metrics_view`) -> `tests/backend/test_health_metrics.py`
