"""Load deterministic ingredient rules and synthetic seed recipes into the database."""

import json
from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import IngredientRule, Recipe, RecipeIngredient, UserDietaryProfile


class Command(BaseCommand):
    """Seed IngredientRule, synthetic Recipes, and default UserDietaryProfile."""

    help = "Seed deterministic ingredient rules and synthetic sample recipes."

    def handle(self, *args, **options):
        rules_path = settings.DATA_DIR / "ingredient_rules.json"
        recipes_path = settings.DATA_DIR / "seed_recipes.json"

        with open(rules_path, encoding="utf-8") as f:
            rules_data = json.load(f)

        rules_created = 0
        for entry in rules_data:
            _, created = IngredientRule.objects.update_or_create(
                canonical_name=entry["canonical_name"],
                defaults={
                    "aliases": entry.get("aliases", []),
                    "allergens": entry.get("allergens", []),
                    "dietary_incompatible": entry.get("dietary_incompatible", []),
                    "allowed_substitutes": entry.get("allowed_substitutes", []),
                    "is_ambiguous": entry.get("is_ambiguous", False),
                    "ambiguity_reason": entry.get("ambiguity_reason", ""),
                    "notes": entry.get("notes", ""),
                },
            )
            if created:
                rules_created += 1

        with open(recipes_path, encoding="utf-8") as f:
            recipes_data = json.load(f)

        recipes_created = 0
        for item in recipes_data:
            if Recipe.objects.filter(share_token=item["share_token"]).exists():
                continue
            recipe = Recipe.objects.create(
                title=item["title"],
                author_name=item["author_name"],
                description=item.get("description", ""),
                instructions=item["instructions"],
                prep_time_minutes=item.get("prep_time_minutes", 20),
                servings=item.get("servings", 2),
                dietary_tags=item.get("dietary_tags", []),
                is_public=item.get("is_public", True),
                share_token=item["share_token"],
            )
            for ing in item.get("ingredients", []):
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    name=ing["name"],
                    quantity=ing.get("quantity", ""),
                    unit=ing.get("unit", ""),
                    notes=ing.get("notes", ""),
                )
            recipes_created += 1

        UserDietaryProfile.objects.get_or_create(profile_key="default")

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(rules_data)} rules ({rules_created} new) and {recipes_created} new synthetic recipes."
            )
        )
