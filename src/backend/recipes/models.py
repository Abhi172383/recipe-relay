"""Database models for RecipeRelay."""

import secrets
import uuid
from django.db import models
from django.utils.text import slugify


def normalize_ingredient_name(name: str) -> str:
    """Normalize an ingredient string for deterministic alias lookup."""
    return " ".join(name.strip().lower().split())


def generate_share_token() -> str:
    """Generate a URL-safe short share token for public recipes."""
    return secrets.token_urlsafe(8)


class Recipe(models.Model):
    """A shared recipe created by a home cook or food blogger."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=210, unique=True, blank=True)
    author_name = models.CharField(max_length=120, default="Home Cook (Synthetic)")
    description = models.TextField(blank=True)
    instructions = models.TextField()
    prep_time_minutes = models.PositiveIntegerField(default=20)
    servings = models.PositiveIntegerField(default=2)
    dietary_tags = models.JSONField(default=list, blank=True)
    is_public = models.BooleanField(default=True)
    share_token = models.CharField(
        max_length=64, unique=True, default=generate_share_token
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "title"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:180] or "recipe"
            candidate = base
            counter = 1
            while Recipe.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{counter}"
                counter += 1
            self.slug = candidate
        if not self.share_token:
            self.share_token = generate_share_token()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title


class RecipeIngredient(models.Model):
    """Structured ingredient row belonging to a Recipe."""

    recipe = models.ForeignKey(
        Recipe, related_name="ingredients", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=140)
    normalized_name = models.CharField(max_length=140, blank=True, db_index=True)
    quantity = models.CharField(max_length=50, blank=True)
    unit = models.CharField(max_length=50, blank=True)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["id"]

    def save(self, *args, **kwargs):
        self.normalized_name = normalize_ingredient_name(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        parts = [self.quantity, self.unit, self.name]
        return " ".join(p for p in parts if p).strip()


class UserDietaryProfile(models.Model):
    """Stores dietary preferences and allergy exclusions for a profile key."""

    profile_key = models.CharField(max_length=80, unique=True, default="default")
    allergies = models.JSONField(default=list, blank=True)
    dietary_preferences = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Profile({self.profile_key})"


class IngredientRule(models.Model):
    """Deterministic safety rule table validating all LLM substitution candidates."""

    canonical_name = models.CharField(max_length=140, unique=True, db_index=True)
    aliases = models.JSONField(default=list, blank=True)
    allergens = models.JSONField(default=list, blank=True)
    dietary_incompatible = models.JSONField(default=list, blank=True)
    allowed_substitutes = models.JSONField(default=list, blank=True)
    is_ambiguous = models.BooleanField(default=False)
    ambiguity_reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["canonical_name"]

    def save(self, *args, **kwargs):
        self.canonical_name = normalize_ingredient_name(self.canonical_name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.canonical_name


class SubstitutionAuditLog(models.Model):
    """Audit record capturing LLM proposals and deterministic validation outcomes."""

    requested_ingredient = models.CharField(max_length=140)
    resolved_canonical = models.CharField(max_length=140, blank=True)
    active_allergies = models.JSONField(default=list, blank=True)
    active_diets = models.JSONField(default=list, blank=True)
    provider_used = models.CharField(max_length=50, default="mock")
    raw_candidates = models.JSONField(default=list, blank=True)
    accepted_candidates = models.JSONField(default=list, blank=True)
    rejected_candidates = models.JSONField(default=list, blank=True)
    final_status = models.CharField(max_length=40, default="no_safe_suggestion")
    latency_ms = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.requested_ingredient} -> {self.final_status}"
