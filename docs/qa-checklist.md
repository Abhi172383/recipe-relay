# Quality Assurance (QA) Checklist — RecipeRelay

## Risk-Prioritized Testing Strategy
1. **P0 (Safety-Critical):** Deterministic allergen & alias rejection (`dairy`, `peanut`, `tree_nut`, `gluten`, `soy`, `egg`, `shellfish`, `sesame`), safe fallback on missing/ambiguous rules, zero unverified LLM leaks.
2. **P1 (Core Functional):** Recipe CRUD, share-token URL resolution, title & alias-aware ingredient search, `/api/health/` and `/api/metrics/`.
3. **P2 (UI & Accessibility):** React Vitest suite, Selenium Page Object Model end-to-end journey, keyboard focus & ARIA live regions.

## Pre-Release QA Checklist
- [x] Synthetic-only seed data (`data/seed_recipes.json`); zero real PII.
- [x] `.env.example` contains variable names only; `.env` is gitignored.
- [x] `flake8` backend & test linting passes with 0 errors.
- [x] Backend pytest suite passes with >= 80% statement coverage (actual measured: 94%; enforced in CI via coverage.xml).
- [x] 40-case substitution evaluation meets 100% allergy safety and >= 80% acceptance.
- [x] React Vitest suite and production `vite build` pass.
- [x] Selenium Page-Object end-to-end journey passes in headless Chrome.
- [x] SonarQube `sonar-project.properties`, GitHub Actions CI, and `Jenkinsfile` configured.
