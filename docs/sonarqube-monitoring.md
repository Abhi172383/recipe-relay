# SonarQube Configuration & Monitoring Guide

## 1. SonarQube Setup
Project configuration is defined in [sonar-project.properties](../sonar-project.properties):
- `sonar.projectKey=reciperelay`
- `sonar.sources=src/backend/recipes,src/frontend/src`
- `sonar.tests=tests/backend,src/frontend/src/__tests__`
- `sonar.exclusions=**/migrations/**,**/node_modules/**,**/dist/**,**/staticfiles/**`
- `sonar.python.coverage.reportPaths=coverage.xml`

### Quality Gate Targets
- **Blocker / Critical Issues:** 0
- **Test Coverage:** >= 80%
- **Security Hotspots:** 0 unreviewed (no hardcoded secrets; ORM parameterized queries only)
- **Code Duplication:** < 3%

### Running Locally with SonarScanner (Optional)
1. Start SonarQube locally (e.g., `docker run -d --name sonarqube -p 9000:9000 sonarqube:lts-community`).
2. Generate `coverage.xml`:
   ```bash
   USE_SQLITE=true .venv/bin/coverage run -m pytest
   .venv/bin/coverage xml -o coverage.xml
   ```
3. Run scanner:
   ```bash
   sonar-scanner -Dsonar.host.url=http://localhost:9000 -Dsonar.token=$SONAR_TOKEN
   ```

In GitHub Actions (`.github/workflows/ci.yml`), the `sonarqube-scan` job runs automatically whenever `SONAR_TOKEN` and `SONAR_HOST_URL` repository secrets are configured.

---

## 2. Health & Metrics Monitoring Guidance

### Health Endpoint: `GET /api/health/`
Checks:
1. Live database query (`SELECT 1`) and reports `database_vendor` (`postgresql` or `sqlite`).
2. Number of deterministic safety rules loaded (`rules_loaded`). If `rules_loaded == 0`, status drops to `"degraded"` so load balancers do not route substitution traffic to an unseeded database.
3. Active `llm_provider` (`mock`, `openai`, `gemini`, or `openai_compatible`).

### Metrics Endpoint: `GET /api/metrics/` (and `?output=prometheus`)
Exposes:
- `reciperelay_recipes_total`
- `reciperelay_rules_total`
- `reciperelay_substitution_requests_total`
- `reciperelay_substitution_verified_total`
- `reciperelay_substitution_no_safe_total`
- `reciperelay_rejected_candidates_total`
- `reciperelay_substitution_avg_latency_ms`

### Recommended Alerting Rules
- **Health Degraded:** Alert if `GET /api/health/` returns non-200 or `rules_loaded == 0`.
- **High Rejection Spike:** Investigate if `reciperelay_rejected_candidates_total` spikes sharply when using an external LLM (indicates prompt drift or model proposing unsafe ingredients).
- **Latency:** Alert if `reciperelay_substitution_avg_latency_ms > 3000` ms.
