"""Reproducible 40-case evaluation script for RecipeRelay ingredient substitution safety and acceptance.

Usage:
    USE_SQLITE=true .venv/bin/python tests/evaluate_substitutions.py
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "src" / "backend"
sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reciperelay.settings")
os.environ.setdefault("USE_SQLITE", "true")

import django  # noqa: E402

django.setup()

from django.core.management import call_command  # noqa: E402
from rest_framework.test import APIClient  # noqa: E402
from recipes.rules_engine import expand_allergens  # noqa: E402


def run_evaluation() -> int:
    """Execute all 40 cases via the DRF API and write actual results to evidence/phase4/."""
    call_command("migrate", verbosity=0)
    call_command("seed_data", verbosity=0)

    eval_path = REPO_ROOT / "data" / "evaluation_cases.json"
    with open(eval_path, encoding="utf-8") as f:
        cases = json.load(f)

    client = APIClient()
    results = []
    allergy_safe_count = 0
    accepted_count = 0

    for case in cases:
        payload = {
            "ingredient": case["ingredient"],
            "allergies": case["allergies"],
            "dietary_preferences": case["dietary_preferences"],
            "inject_unsafe_candidates": case.get("inject_unsafe_candidates", []),
        }
        resp = client.post("/api/substitutions/suggest/", payload, format="json")
        body = resp.json()

        forbidden = expand_allergens(case.get("forbidden_allergens", []))
        leaked_allergens = []
        for sug in body.get("suggestions", []):
            sug_allergens = expand_allergens(sug.get("allergens", []))
            overlap = sorted(sug_allergens.intersection(forbidden))
            if overlap:
                leaked_allergens.append({"substitute": sug["name"], "overlap": overlap})

        is_allergy_safe = len(leaked_allergens) == 0 and body.get("ai_assisted") is True
        status_matches = body.get("status") == case["expected_status"]
        has_valid_outcome = status_matches and (
            len(body.get("suggestions", [])) > 0
            if case["expected_status"] == "verified"
            else len(body.get("suggestions", [])) == 0
        )

        if is_allergy_safe:
            allergy_safe_count += 1
        if is_allergy_safe and has_valid_outcome:
            accepted_count += 1

        results.append(
            {
                "id": case["id"],
                "ingredient": case["ingredient"],
                "allergies": case["allergies"],
                "dietary_preferences": case["dietary_preferences"],
                "expected_status": case["expected_status"],
                "actual_status": body.get("status"),
                "suggestions": [s["name"] for s in body.get("suggestions", [])],
                "rejected_candidates": body.get("rejected_candidates", []),
                "allergy_safe": is_allergy_safe,
                "case_passed": is_allergy_safe and has_valid_outcome,
                "leaked_allergens": leaked_allergens,
                "description": case["description"],
            }
        )

    total = len(cases)
    safety_pct = round((allergy_safe_count / total) * 100.0, 2) if total else 0.0
    acceptance_pct = round((accepted_count / total) * 100.0, 2) if total else 0.0

    summary = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_cases": total,
        "allergy_safe_cases": allergy_safe_count,
        "allergy_safety_rate_pct": safety_pct,
        "accepted_cases": accepted_count,
        "acceptance_rate_pct": acceptance_pct,
        "targets": {
            "allergy_safety_target_pct": 100.0,
            "acceptance_target_pct": 80.0,
            "allergy_safety_target_met": safety_pct == 100.0,
            "acceptance_target_met": acceptance_pct >= 80.0,
        },
        "cases": results,
    }

    out_dir = REPO_ROOT / "evidence" / "phase4"
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    lines = [
        "# Substitution Evaluation Report (40 Cases)",
        "",
        f"- **Run Timestamp (UTC):** {summary['timestamp_utc']}",
        f"- **Total Cases:** {total}",
        f"- **Allergy-Safe Cases:** {allergy_safe_count}/{total} ({safety_pct}%) — Target: 100%",
        f"- **Rule-Validated Acceptance:** {accepted_count}/{total} ({acceptance_pct}%) — Target: >= 80%",
        "",
        "| Case ID | Ingredient | Expected | Actual | Safe? | Pass? | Verified Suggestions |",
        "|---------|------------|----------|--------|-------|-------|----------------------|",
    ]
    for r in results:
        sugs = ", ".join(r["suggestions"]) if r["suggestions"] else "*(none - safe fallback)*"
        lines.append(
            f"| {r['id']} | {r['ingredient']} | {r['expected_status']} | {r['actual_status']} | "
            f"{'YES' if r['allergy_safe'] else 'NO'} | {'PASS' if r['case_passed'] else 'FAIL'} | {sugs} |"
        )

    with open(out_dir / "evaluation_summary.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(
        f"Evaluation complete: {accepted_count}/{total} passed ({acceptance_pct}%), "
        f"allergy safety {allergy_safe_count}/{total} ({safety_pct}%)."
    )
    return 0 if (safety_pct == 100.0 and acceptance_pct >= 80.0) else 1


if __name__ == "__main__":
    raise SystemExit(run_evaluation())
