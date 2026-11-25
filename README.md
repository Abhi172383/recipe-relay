# RecipeRelay: Recipe Sharing with Ingredient Substitution

A full-stack **AI in Software Engineering (P43)** project enabling home cooks and food bloggers to upload, search, and share recipes while discovering **AI-assisted ingredient substitutions** gated by a **deterministic PostgreSQL safety rules table**.

---

## Mandatory Stack
- **Frontend:** React 18 + Vite + Vitest + React Testing Library
- **Backend:** Python 3.11 + Django 5.1 + Django REST Framework + Gunicorn
- **Database:** PostgreSQL 16 (with explicit `USE_SQLITE=true` quick-test fallback for local CI/unit runs)
- **LLM Adapter:** Configurable (`mock`, `openai`, `gemini`, `openai_compatible`) with automatic safe `mock-fallback`
- **DevOps & Quality:** Docker, Docker Compose, GitHub Actions CI/CD, Jenkinsfile, SonarQube (`sonar-project.properties`), flake8, coverage, Selenium (Page Object Model)

---

## Core Safety Architecture
**Never treat LLM output as inherently safe.**
1. The configurable LLM adapter proposes candidate substitutes with conversion ratios and brief rationales.
2. `DeterministicRuleValidator` (`src/backend/recipes/rules_engine.py`) checks every candidate against the `IngredientRule` table (`data/ingredient_rules.json`):
   - Normalizes **ingredient aliases** (e.g., `scallions` -> `green onion`, `casein` -> `whey protein` -> `dairy`, `groundnut oil` -> `peanut oil`).
   - Rejects **allergen conflicts** and **dietary incompatibilities** (`vegan`, `vegetarian`, `dairy-free`, `gluten-free`, `nut-free`).
   - Fails closed (`no_safe_suggestion`) when a rule is **missing** or marked **ambiguous** (`flour`, `oil`, `stock`).
3. The UI labels every result **AI-Assisted**, displays the verification badge, and shows a cross-contamination limitations notice.

---

## Repository Structure
```text
recipe-relay/
├── .env.example                 # Environment variable names only (no secrets)
├── .github/workflows/ci.yml     # GitHub Actions CI/CD with PostgreSQL service
├── Dockerfile                   # Backend container image
├── Jenkinsfile                  # Declarative Jenkins CI/CD pipeline
├── docker-compose.yml           # PostgreSQL + Django + React/Nginx stack
├── sonar-project.properties     # SonarQube scanner configuration
├── data/                        # Deterministic rules, synthetic recipes, 40-eval cases
├── docs/                        # SRS, Agile plan, Mermaid diagrams, UI prototype, logs, report
├── evidence/phase1..phase5/     # Reproducible outputs & phase evidence
├── src/
│   ├── backend/                 # Django project (reciperelay) & app (recipes)
│   └── frontend/                # React + Vite SPA
└── tests/
    ├── backend/                 # Risk-prioritized pytest unit & integration tests
    ├── selenium/                # Page Object Model E2E browser journey
    └── evaluate_substitutions.py# 40-case safety & acceptance evaluation script
```

---

## Quick Start

### Option A: Docker Compose (Recommended Full PostgreSQL Stack)
```bash
cp .env.example .env
docker compose up --build
```
- Frontend: http://localhost:3000
- Backend API & Health: http://localhost:8000/api/health/
- Operational Metrics: http://localhost:8000/api/metrics/ (or `?output=prometheus`)

### Option B: Local Development (Python + Node)
1. **Configure Environment:**
   ```bash
   cp .env.example .env
   # For quick local run without PostgreSQL installed locally, set USE_SQLITE=true in .env
   ```
2. **Backend Setup:**
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   USE_SQLITE=true .venv/bin/python src/backend/manage.py migrate
   USE_SQLITE=true .venv/bin/python src/backend/manage.py seed_data
   USE_SQLITE=true .venv/bin/python src/backend/manage.py runserver 127.0.0.1:8000
   ```
3. **Frontend Setup:**
   ```bash
   cd src/frontend
   npm install
   npm run dev
   ```
   Open http://localhost:5173

---

## Running Tests, Coverage, Evaluation & Selenium E2E

```bash
# 1. Lint backend & tests
.venv/bin/flake8 src/backend/recipes tests/backend tests/selenium --max-line-length=120 --exclude=migrations

# 2. Backend unit/integration tests + coverage report (fails if < 80%)
USE_SQLITE=true .venv/bin/coverage run -m pytest
.venv/bin/coverage report -m
.venv/bin/coverage xml -o coverage.xml

# 3. 40-case safety & acceptance evaluation (writes evidence/phase4/evaluation_*)
USE_SQLITE=true .venv/bin/python tests/evaluate_substitutions.py

# 4. Frontend unit tests & build
cd src/frontend && npm test && npm run build

# 5. Selenium Page-Object end-to-end browser journey (requires Google Chrome)
.venv/bin/python tests/run_selenium_e2e.py
```

---

## Manual / External Actions Required for Production Use
1. **Real LLM API Key (Optional):** By default `LLM_PROVIDER=mock` runs offline safely. To call OpenAI or Gemini, set `LLM_PROVIDER=openai` (or `gemini`) and `LLM_API_KEY=<your-key>` in `.env` (never commit `.env`).
2. **PostgreSQL & Docker Desktop:** Ensure Docker Desktop (or a local PostgreSQL 16 instance) is running before running `docker compose up --build`.
3. **GitHub Actions Secrets (for SonarQube):** Add `SONAR_TOKEN` and `SONAR_HOST_URL` in GitHub repository Secrets to enable the optional `sonarqube-scan` CI job.
4. **Live UI Screenshots:** Capture manual browser screenshots into `evidence/` during your live demo/viva if required by your instructor.
