# System Diagrams — RecipeRelay

## 1. System Architecture Diagram

```mermaid
flowchart LR
    U["Home Cook / Blogger (Browser)"] -->|"HTTP / Accessible UI"| FE["React Frontend (Vite + Nginx)"]
    FE -->|"REST JSON /api/*"| API["Django REST Framework API"]
    API -->|"ORM Queries"| DB[("PostgreSQL 16 Database")]
    API -->|"Candidate Prompt"| LLM["Configurable LLM Provider (Mock / OpenAI / Gemini)"]
    LLM -->|"Raw Candidates (Untrusted)"| VAL["Deterministic Rules Validator"]
    DB -->|"IngredientRule Table (Aliases & Allergens)"| VAL
    VAL -->|"Verified Safe Swaps or Safe Fallback"| API
    VAL -->|"Audit Record"| DB
    API -->|"Health & Metrics"| MON["/api/health/ & /api/metrics/"]
```

---

## 2. Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    RECIPE ||--o{ RECIPE_INGREDIENT : contains
    RECIPE {
        uuid id PK
        string title
        string slug
        string author_name
        text description
        text instructions
        int prep_time_minutes
        int servings
        json dietary_tags
        bool is_public
        string share_token UK
        datetime created_at
        datetime updated_at
    }
    RECIPE_INGREDIENT {
        int id PK
        uuid recipe_id FK
        string name
        string normalized_name
        string quantity
        string unit
        string notes
    }
    USER_DIETARY_PROFILE {
        string profile_key PK
        json allergies
        json dietary_preferences
        datetime updated_at
    }
    INGREDIENT_RULE {
        int id PK
        string canonical_name UK
        json aliases
        json allergens
        json dietary_incompatible
        json allowed_substitutes
        bool is_ambiguous
        string ambiguity_reason
        text notes
    }
    SUBSTITUTION_AUDIT_LOG {
        int id PK
        string requested_ingredient
        string resolved_canonical
        json active_allergies
        json active_diets
        string provider_used
        json raw_candidates
        json accepted_candidates
        json rejected_candidates
        string final_status
        float latency_ms
        datetime created_at
    }
```

---

## 3. Use-Case Diagram

```mermaid
flowchart TB
    HC(["Home Cook"])
    FB(["Food Blogger"])
    QA(["QA / Safety Reviewer"])

    subgraph RecipeRelay["RecipeRelay System"]
        UC1(("Browse & Search Recipes"))
        UC2(("Create / Edit / Delete Recipe"))
        UC3(("Share Recipe via Token URL"))
        UC4(("Configure Allergies & Diet Profile"))
        UC5(("Request AI Ingredient Substitution"))
        UC6(("Deterministic Rule & Alias Validation"))
        UC7(("Inspect Health, Metrics & Audit Logs"))
    end

    HC --> UC1
    HC --> UC3
    HC --> UC4
    HC --> UC5
    FB --> UC1
    FB --> UC2
    FB --> UC3
    UC5 -.->|"<<include>>"| UC6
    QA --> UC7
    QA --> UC6
```

---

## 4. Substitution Validation Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant UI as React UI
    participant API as Django /substitutions/suggest/
    participant LLM as LLM Adapter (Mock/API)
    participant Rules as DeterministicRuleValidator
    participant DB as PostgreSQL (IngredientRule)

    User->>UI: Click "Substitute" on ingredient (e.g., butter)
    UI->>API: POST {ingredient, allergies: ["dairy"], dietary_preferences: ["vegan"]}
    API->>LLM: Generate candidate swaps with ratio & rationale
    LLM-->>API: Candidates [ghee, olive oil, coconut oil, mystery spread]
    API->>Rules: validate(ingredient, candidates, allergies, diets)
    Rules->>DB: Lookup canonical rules & aliases
    DB-->>Rules: Rules for butter, ghee (allergen: dairy), olive oil (safe), etc.
    Rules->>Rules: Reject ghee (dairy conflict); Reject mystery spread (no rule)
    Rules-->>API: Accepted [olive oil, coconut oil], Rejected [ghee, mystery spread]
    API->>DB: Save SubstitutionAuditLog
    API-->>UI: 200 OK {ai_assisted: true, status: "verified", suggestions: [...], limitations: "..."}
    UI-->>User: Display verified swaps + AI-assisted badge + disclaimer
```
