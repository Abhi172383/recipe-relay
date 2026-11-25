# UI Prototype Overview

A low-fidelity interactive HTML wireframe is available at [docs/ui-prototype.html](ui-prototype.html).

## Key Screen Flows Prototyped
1. **Top Navigation & Safety Banner:** Shows active user allergies and dietary preferences at all times so users never forget which filters govern substitution checks.
2. **Search & Catalog Pane:** Combines title + ingredient search with dietary tag filters and quick access to recipe creation and share links.
3. **Recipe Detail & Inline Substitution Panel:** Lets users click **Suggest Substitute** next to any ingredient, rendering:
   - An **AI-Assisted** label
   - A **Deterministic Rule Verified** or **No Safe Suggestion** status badge
   - Ratio + short culinary rationale
   - Explicit limitations / cross-contamination disclaimer
4. **Dietary Preferences Sidebar / Modal:** Checkbox toggles for common allergens (`dairy`, `peanut`, `tree_nut`, `gluten`, `egg`, `soy`, `shellfish`, `sesame`) and diets (`vegan`, `vegetarian`, `dairy-free`, `gluten-free`, `nut-free`).
