# Final Project Report & PPT Starter Content
## RecipeRelay: Recipe Sharing with Ingredient Substitution

> **Note:** Populate the measured metrics table below strictly from verified command outputs after running the test and evaluation scripts in this environment.

---

## Part A: Executive Summary & Final Report

### 1. Problem Statement
Home cooks and food bloggers frequently share recipes online, yet adapting those recipes for food allergies or dietary preferences is error-prone. Directly asking a generative LLM for ingredient swaps introduces severe safety risks: LLMs may overlook hidden allergens (e.g., *ghee* or *whey* for dairy allergy, *tamari* for soy allergy) or invent unverified substitutes.

### 2. Solution Architecture
**RecipeRelay** pairs a React frontend and Django REST + PostgreSQL backend with a **two-stage substitution pipeline**:
1. **Candidate Generation (LLM Adapter):** Configurable adapter supporting `mock` (offline safe default), `openai`, `gemini`, and `openai_compatible` endpoints.
2. **Deterministic Safety Gate (`DeterministicRuleValidator`):** Validates every candidate against a PostgreSQL `IngredientRule` table covering canonical names, aliases, allergen sets, dietary tags, and ambiguity flags. Unknown or ambiguous ingredients fail closed (`no_safe_suggestion`).

### 3. Agile Delivery & Git Engineering
- **Sprint 1:** Recipe CRUD, structured ingredients, unique share links, title/ingredient search, synthetic dataset.
- **Sprint 2:** Dietary/allergy profile, LLM adapter + deterministic rules engine, AI-assisted & limitations UI, `/api/health/` & `/api/metrics/`, Selenium POM journey, Docker/CI/Jenkins/SonarQube.
- **Git Workflow:** Feature branches (`feat/sprint1-recipes`, `feat/sprint2-substitutions`), PR-style merges, and a documented planned merge-conflict exercise (`docs/merge-conflict-exercise.md`).

### 4. Known Limitations & Future Work
- Deterministic rule coverage currently spans 47 canonical ingredient/substitute entries; expanding to a larger culinary ontology requires curated dietitian/food-safety review.
- Packaged foods can still carry factory cross-contamination; the UI explicitly reminds users to verify product labels.
- Multi-user authentication (JWT/OAuth) is scoped as a future enhancement beyond the single-profile/keyed-profile MVP.

---

## Part B: Viva / PPT Slide-by-Slide Starter Content

### Slide 1 — Title
- **Title:** RecipeRelay: Recipe Sharing with Ingredient Substitution
- **Subtitle:** AI in Software Engineering (P43) — Safety-Gated LLM Architecture
- **Stack:** React, Django REST Framework, PostgreSQL, Docker, GitHub Actions, Jenkins, Selenium, SonarQube

### Slide 2 — Problem & Safety Risk
- Why raw LLM output cannot be trusted for allergies (hidden derivatives, aliases like *groundnut*/*casein*, hallucinated swaps).
- Core design rule: **LLM proposes; deterministic PostgreSQL rules decide.**

### Slide 3 — System Architecture & ER Model
- Show Mermaid Architecture & ER diagrams from [docs/diagrams.md](diagrams.md).
- Highlight `Recipe`, `RecipeIngredient`, `IngredientRule`, `UserDietaryProfile`, `SubstitutionAuditLog`.

### Slide 4 — Two-Sprint Agile Plan
- Sprint 1: Recipe CRUD, sharing tokens, title & alias-aware ingredient search.
- Sprint 2: Dietary/allergy profile, LLM adapter (`mock`/API), deterministic validator, observability.

### Slide 5 — Deterministic Rules Engine (Live Demo Talking Point)
- Alias resolution (`scallions` -> `green onion`, `casein` -> `whey protein` -> `dairy`).
- Safe fail-closed behavior for ambiguous (`flour`, `oil`, `stock`) and unknown ingredients.
- Transparency: **AI-Assisted** badge + rejected candidate list + limitations disclaimer.

### Slide 6 — Quality Assurance, CI/CD & Evaluation
- Risk-prioritized pytest suite, coverage report, flake8 lint, Vitest frontend tests, Selenium Page Object Model journey.
- 40-case reproducible evaluation (`tests/evaluate_substitutions.py`) measuring allergy safety and rule-validated acceptance.
- GitHub Actions (`postgres` service) + `Jenkinsfile` + SonarQube (`sonar-project.properties`).
