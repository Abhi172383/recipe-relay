"""Django admin registrations for RecipeRelay."""

from django.contrib import admin
from .models import (
    IngredientRule,
    Recipe,
    RecipeIngredient,
    SubstitutionAuditLog,
    UserDietaryProfile,
)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ["title", "author_name", "prep_time_minutes", "servings", "is_public"]
    search_fields = ["title", "author_name"]
    inlines = [RecipeIngredientInline]


@admin.register(IngredientRule)
class IngredientRuleAdmin(admin.ModelAdmin):
    list_display = ["canonical_name", "is_ambiguous"]
    search_fields = ["canonical_name"]


@admin.register(UserDietaryProfile)
class UserDietaryProfileAdmin(admin.ModelAdmin):
    list_display = ["profile_key", "updated_at"]


@admin.register(SubstitutionAuditLog)
class SubstitutionAuditLogAdmin(admin.ModelAdmin):
    list_display = ["requested_ingredient", "resolved_canonical", "final_status", "provider_used", "created_at"]
