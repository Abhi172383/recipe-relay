"""Deterministic ingredient rules engine for validating LLM substitution candidates.

Safety principle: Never treat LLM output as inherently safe.
Every candidate must be resolved against the IngredientRule database table,
checked for alias-resolved allergens and dietary incompatibilities, and
rejected if unknown, ambiguous, or unsafe.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from .models import IngredientRule, normalize_ingredient_name

AI_LIMITATIONS_NOTICE = (
    "AI-assisted suggestion verified against RecipeRelay's deterministic allergen "
    "and alias rules table. Always verify packaged product labels for hidden "
    "ingredients or factory cross-contamination."
)

ALLERGEN_SYNONYMS: Dict[str, Set[str]] = {
    "dairy": {"dairy", "milk", "lactose"},
    "milk": {"dairy", "milk", "lactose"},
    "lactose": {"dairy", "milk", "lactose"},
    "peanut": {"peanut", "peanuts", "groundnut"},
    "peanuts": {"peanut", "peanuts", "groundnut"},
    "tree_nut": {"tree_nut", "tree nut", "tree nuts", "nuts"},
    "tree nut": {"tree_nut", "tree nut", "tree nuts", "nuts"},
    "tree nuts": {"tree_nut", "tree nut", "tree nuts", "nuts"},
    "nuts": {"tree_nut", "peanut", "nuts"},
    "gluten": {"gluten", "wheat"},
    "wheat": {"gluten", "wheat"},
    "egg": {"egg", "eggs"},
    "eggs": {"egg", "eggs"},
    "soy": {"soy", "soya", "soybean"},
    "shellfish": {"shellfish", "crustacean"},
    "fish": {"fish"},
    "sesame": {"sesame"},
}

DIET_IMPLIED_EXCLUDED_ALLERGENS: Dict[str, Set[str]] = {
    "vegan": {"dairy", "egg", "fish", "shellfish"},
    "vegetarian": {"fish", "shellfish"},
    "dairy-free": {"dairy"},
    "gluten-free": {"gluten", "wheat"},
    "nut-free": {"peanut", "tree_nut"},
}


@dataclass
class ValidationOutcome:
    """Structured result from deterministic candidate validation."""

    status: str  # "verified" | "no_safe_suggestion"
    requested_ingredient: str
    resolved_canonical: Optional[str]
    accepted: List[dict]
    rejected: List[dict]
    message: str
    ai_assisted: bool = True
    limitations: str = AI_LIMITATIONS_NOTICE


def expand_allergens(raw_allergies: List[str]) -> Set[str]:
    """Expand user-supplied allergy terms to canonical allergen tokens."""
    expanded: Set[str] = set()
    for item in raw_allergies:
        norm = normalize_ingredient_name(item).replace("-", " ")
        if not norm:
            continue
        expanded.add(norm)
        expanded.add(norm.replace(" ", "_"))
        if norm in ALLERGEN_SYNONYMS:
            expanded.update(ALLERGEN_SYNONYMS[norm])
    return expanded


def normalize_diets(raw_diets: List[str]) -> Set[str]:
    """Normalize dietary preference strings."""
    return {normalize_ingredient_name(d) for d in raw_diets if normalize_ingredient_name(d)}


class DeterministicRuleValidator:
    """Validates candidate substitutions against PostgreSQL IngredientRule records."""

    def __init__(self, rules: Optional[List[IngredientRule]] = None):
        if rules is None:
            rules = list(IngredientRule.objects.all())
        self.rules_by_key: Dict[str, IngredientRule] = {}
        for rule in rules:
            self.rules_by_key[normalize_ingredient_name(rule.canonical_name)] = rule
            for alias in rule.aliases or []:
                self.rules_by_key[normalize_ingredient_name(alias)] = rule

    def resolve_rule(self, ingredient_name: str) -> Optional[IngredientRule]:
        """Resolve an ingredient or alias to its canonical IngredientRule."""
        return self.rules_by_key.get(normalize_ingredient_name(ingredient_name))

    def validate(
        self,
        ingredient_name: str,
        candidates: List[dict],
        allergies: Optional[List[str]] = None,
        dietary_preferences: Optional[List[str]] = None,
    ) -> ValidationOutcome:
        """Validate LLM candidate substitutions deterministically."""
        allergies = allergies or []
        dietary_preferences = dietary_preferences or []

        active_diets = normalize_diets(dietary_preferences)
        excluded_allergens = expand_allergens(allergies)
        for diet in active_diets:
            excluded_allergens.update(DIET_IMPLIED_EXCLUDED_ALLERGENS.get(diet, set()))

        source_rule = self.resolve_rule(ingredient_name)
        if source_rule is None:
            rejected = [
                {
                    "name": c.get("name", ""),
                    "reason": (
                        f"Missing deterministic rule for '{ingredient_name}'. "
                        "Unknown ingredients cannot be safely substituted."
                    ),
                }
                for c in candidates
            ]
            return ValidationOutcome(
                status="no_safe_suggestion",
                requested_ingredient=ingredient_name,
                resolved_canonical=None,
                accepted=[],
                rejected=rejected,
                message=(
                    f"No verified substitution rule exists for '{ingredient_name}'. "
                    "To protect against hidden allergens, no substitute is shown."
                ),
            )

        if source_rule.is_ambiguous:
            rejected = [
                {
                    "name": c.get("name", ""),
                    "reason": source_rule.ambiguity_reason or "Source ingredient is ambiguous.",
                }
                for c in candidates
            ]
            return ValidationOutcome(
                status="no_safe_suggestion",
                requested_ingredient=ingredient_name,
                resolved_canonical=source_rule.canonical_name,
                accepted=[],
                rejected=rejected,
                message=source_rule.ambiguity_reason
                or f"'{ingredient_name}' is ambiguous. Please specify the exact ingredient.",
            )

        approved_index: Dict[str, dict] = {}
        for sub in source_rule.allowed_substitutes or []:
            sub_norm = normalize_ingredient_name(sub["name"])
            approved_index[sub_norm] = sub
            sub_rule = self.resolve_rule(sub_norm)
            if sub_rule:
                approved_index[sub_rule.canonical_name] = sub
                for alias in sub_rule.aliases or []:
                    approved_index[normalize_ingredient_name(alias)] = sub

        accepted: List[dict] = []
        rejected: List[dict] = []
        seen_accepted: Set[str] = set()

        for cand in candidates:
            cand_name = str(cand.get("name", "")).strip()
            cand_norm = normalize_ingredient_name(cand_name)
            if not cand_norm:
                continue

            cand_rule = self.resolve_rule(cand_norm)
            approved_entry = approved_index.get(cand_norm)
            if not approved_entry and cand_rule:
                approved_entry = approved_index.get(cand_rule.canonical_name)

            # Collect all known allergens from both the approved substitute entry and candidate rule
            cand_allergens: Set[str] = set()
            if approved_entry:
                cand_allergens.update(expand_allergens(approved_entry.get("allergens", [])))
            if cand_rule:
                cand_allergens.update(expand_allergens(cand_rule.allergens or []))

            allergen_conflicts = sorted(cand_allergens.intersection(excluded_allergens))
            if allergen_conflicts:
                rejected.append(
                    {
                        "name": cand_name,
                        "reason": f"Allergen/diet exclusion conflict: {', '.join(allergen_conflicts)}",
                    }
                )
                continue

            if not approved_entry:
                rejected.append(
                    {
                        "name": cand_name,
                        "reason": (
                            f"Candidate '{cand_name}' is not in the verified substitution "
                            f"rules table for '{source_rule.canonical_name}'."
                        ),
                    }
                )
                continue

            # Check dietary preference tags
            cand_tags = {normalize_ingredient_name(t) for t in approved_entry.get("dietary_tags", [])}
            cand_incompat = set()
            if cand_rule:
                cand_incompat = {
                    normalize_ingredient_name(d)
                    for d in (cand_rule.dietary_incompatible or [])
                }

            missing_diets = sorted(
                d for d in active_diets if (d in cand_incompat) or (cand_tags and d not in cand_tags)
            )
            if missing_diets:
                rejected.append(
                    {
                        "name": cand_name,
                        "reason": f"Does not satisfy dietary preference(s): {', '.join(missing_diets)}",
                    }
                )
                continue

            canonical_sub_name = approved_entry["name"]
            if canonical_sub_name in seen_accepted:
                continue
            seen_accepted.add(canonical_sub_name)

            rationale = str(cand.get("rationale") or "").strip() or approved_entry.get("rationale", "")
            accepted.append(
                {
                    "name": canonical_sub_name,
                    "ratio": approved_entry.get("ratio", cand.get("ratio", "1:1")),
                    "rationale": rationale,
                    "allergens": approved_entry.get("allergens", []),
                    "dietary_tags": approved_entry.get("dietary_tags", []),
                    "rule_verified": True,
                }
            )

        if not accepted:
            return ValidationOutcome(
                status="no_safe_suggestion",
                requested_ingredient=ingredient_name,
                resolved_canonical=source_rule.canonical_name,
                accepted=[],
                rejected=rejected,
                message=(
                    f"No safe verified substitution found for '{source_rule.canonical_name}' "
                    "matching your active allergy and dietary exclusions."
                ),
            )

        return ValidationOutcome(
            status="verified",
            requested_ingredient=ingredient_name,
            resolved_canonical=source_rule.canonical_name,
            accepted=accepted,
            rejected=rejected,
            message=(
                f"Found {len(accepted)} rule-verified substitution(s) for "
                f"'{source_rule.canonical_name}'."
            ),
        )
