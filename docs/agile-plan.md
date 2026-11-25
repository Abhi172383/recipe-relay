# Agile Delivery Plan, User Stories & Acceptance Criteria

## 1. Incremental Delivery Plan (Two One-Week Sprints)

### Sprint 1 (Week 1): Recipe Upload, CRUD, Search & Sharing
**Sprint Goal:** Deliver a working full-stack recipe repository where home cooks and bloggers can create, edit, delete, search, and share synthetic recipes.
- **S1-1:** Django REST API + PostgreSQL schema (`Recipe`, `RecipeIngredient`, migrations, synthetic seed loader).
- **S1-2:** Recipe CRUD & share token endpoints (`GET/POST /api/recipes/`, `GET/PUT/DELETE /api/recipes/<id>/`, `GET /api/recipes/share/<token>/`).
- **S1-3:** Search endpoint supporting title and ingredient filtering (`?q=`, `?ingredient=`, `?diet=`).
- **S1-4:** React UI for recipe browsing, search bar, recipe creation/edit form, detail page, and copyable share link.
- **S1-5:** Sprint 1 unit/integration tests and CI workflow baseline.

### Sprint 2 (Week 2): AI Substitution, Dietary Filters & Deterministic Safety Gate
**Sprint Goal:** Integrate configurable LLM substitution generation guarded by a deterministic PostgreSQL rules engine, dietary/allergy profiles, observability, and Selenium E2E verification.
- **S2-1:** `IngredientRule`, `UserDietaryProfile`, and `SubstitutionAuditLog` models + seeded deterministic rules table (`data/ingredient_rules.json`).
- **S2-2:** Configurable LLM adapter (`mock` fallback + `openai` / `gemini` / `openai_compatible`) and `DeterministicRuleValidator` (alias normalization, allergen rejection, dietary check, ambiguity fallback).
- **S2-3:** React Dietary Preferences drawer, inline Substitution Panel with **AI-assisted** labeling, limitations banner, and validation audit trace.
- **S2-4:** `/api/health/`, `/api/metrics/`, Selenium Page-Object E2E journey, 40-case evaluation script, SonarQube config, and Jenkinsfile.

---

## 2. User Stories & Acceptance Criteria

### US-1: Create & Share a Recipe (Sprint 1)
> **As a** food blogger, **I want** to publish a recipe with structured ingredients and get a shareable link, **so that** readers can view and cook it easily.

**Acceptance Criteria (Given / When / Then):**
- **Given** I am on the "New Recipe" form, **When** I enter a title, servings, instructions, and at least one ingredient and submit, **Then** the recipe is saved in the database and appears in the recipe catalog.
- **Given** a published recipe detail view, **When** I click "Copy Share Link", **Then** the recipe's unique share URL is copied and an accessible confirmation message is shown.

### US-2: Search by Recipe Title & Ingredients (Sprint 1)
> **As a** home cook, **I want** to search recipes by title or specific ingredients I have on hand, **so that** I can quickly find relevant meals.

**Acceptance Criteria:**
- **Given** seeded recipes exist in the database, **When** I search `"chickpea"` in the ingredient filter or search box, **Then** recipes containing `"chickpea"` (or `"garbanzo beans"` via search/alias) are returned.
- **Given** I enter a title keyword such as `"Pasta"`, **When** the search runs, **Then** matching recipes are displayed and non-matching recipes are excluded.

### US-3: Manage Dietary Preferences & Allergy Exclusions (Sprint 2)
> **As a** cook with food allergies, **I want** to save my allergies (e.g., dairy, peanut) and dietary preferences (e.g., vegan), **so that** substitution suggestions never violate my safety constraints.

**Acceptance Criteria:**
- **Given** the Dietary & Allergy Preferences panel, **When** I select `dairy` and `peanut` allergies and save, **Then** the profile persists across requests via `/api/preferences/` and is visibly active in the header summary.

### US-4: Safe AI-Assisted Ingredient Substitution (Sprint 2)
> **As a** home cook missing an ingredient, **I want** substitution ideas with a brief rationale that are strictly checked against my allergies, **so that** I can adapt recipes safely.

**Acceptance Criteria:**
- **Given** my allergy profile includes `dairy`, **When** I request a substitute for `butter`, **Then** the system rejects dairy candidates (like `ghee` or `greek yogurt`) and only displays rule-verified dairy-free options (like `olive oil` or `coconut oil`) with ratio, rationale, and an **AI-assisted** badge + limitations notice.
- **Given** my allergy profile includes `tree_nut` AND `dairy`, **When** the LLM proposes `almond milk` for `milk`, **Then** the deterministic validator detects `tree_nut` on `almond milk`, rejects it, and only returns safe alternatives (e.g., `oat milk`) or a safe no-suggestion message.

### US-5: Safe Handling of Missing or Ambiguous Rules (Sprint 2)
> **As a** safety-conscious user, **I want** the app to refuse guessing when an ingredient is ambiguous or absent from the safety table, **so that** unverified substitutions are never shown as safe.

**Acceptance Criteria:**
- **Given** an unknown ingredient (e.g., `dragonfruit powder`) or ambiguous ingredient (e.g., `generic mystery sauce`), **When** I request a substitution, **Then** the system returns `status: "no_safe_suggestion"` with a clear, honest explanation and zero unverified substitutes.
