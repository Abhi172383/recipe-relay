"""DRF views and observability endpoints for RecipeRelay."""

import time
from django.conf import settings
from django.db import connection
from django.db.models import Avg, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .llm_provider import generate_substitution_candidates
from .models import (
    IngredientRule,
    Recipe,
    SubstitutionAuditLog,
    UserDietaryProfile,
    normalize_ingredient_name,
)
from .rules_engine import DeterministicRuleValidator
from .serializers import (
    IngredientRuleSerializer,
    RecipeSerializer,
    SubstitutionRequestSerializer,
    UserDietaryProfileSerializer,
)


def _expand_search_terms(term: str) -> set[str]:
    """Expand a search term with known canonical/alias variants for smart ingredient search."""
    norm = normalize_ingredient_name(term)
    terms = {norm}
    for rule in IngredientRule.objects.all():
        all_names = [rule.canonical_name] + [normalize_ingredient_name(a) for a in (rule.aliases or [])]
        if any(norm in name for name in all_names):
            terms.update(all_names)
    return {t for t in terms if t}


class RecipeListCreateView(generics.ListCreateAPIView):
    """List/search recipes by title or ingredient, or create a new recipe."""

    serializer_class = RecipeSerializer

    def get_queryset(self):
        queryset = Recipe.objects.prefetch_related("ingredients").all()
        q = self.request.query_params.get("q", "").strip()
        ingredient = self.request.query_params.get("ingredient", "").strip()
        diet = self.request.query_params.get("diet", "").strip().lower()

        if q:
            expanded = _expand_search_terms(q)
            query_filter = Q(title__icontains=q) | Q(description__icontains=q)
            for term in expanded:
                query_filter |= Q(ingredients__name__icontains=term)
                query_filter |= Q(ingredients__normalized_name__icontains=term)
            queryset = queryset.filter(query_filter).distinct()

        if ingredient:
            expanded_ing = _expand_search_terms(ingredient)
            ing_filter = Q()
            for term in expanded_ing:
                ing_filter |= Q(ingredients__name__icontains=term)
                ing_filter |= Q(ingredients__normalized_name__icontains=term)
            queryset = queryset.filter(ing_filter).distinct()

        if diet:
            matching_ids = [
                r.id
                for r in queryset
                if diet in [str(tag).strip().lower() for tag in (r.dietary_tags or [])]
            ]
            queryset = queryset.filter(id__in=matching_ids)

        return queryset


class RecipeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a specific recipe."""

    queryset = Recipe.objects.prefetch_related("ingredients").all()
    serializer_class = RecipeSerializer


class RecipeShareView(APIView):
    """Retrieve a public recipe using its unique share token."""

    def get(self, request, share_token: str):
        recipe = get_object_or_404(
            Recipe.objects.prefetch_related("ingredients"),
            share_token=share_token,
            is_public=True,
        )
        return Response(RecipeSerializer(recipe).data)


class DietaryProfileView(APIView):
    """Retrieve or update user dietary preferences and allergy exclusions."""

    def get(self, request):
        profile_key = request.query_params.get("profile_key", "default").strip() or "default"
        profile, _ = UserDietaryProfile.objects.get_or_create(profile_key=profile_key)
        return Response(UserDietaryProfileSerializer(profile).data)

    def put(self, request):
        profile_key = (
            request.data.get("profile_key")
            or request.query_params.get("profile_key")
            or "default"
        )
        profile, _ = UserDietaryProfile.objects.get_or_create(profile_key=profile_key)
        serializer = UserDietaryProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class IngredientRuleListView(generics.ListAPIView):
    """Read-only endpoint exposing the deterministic safety rules table."""

    queryset = IngredientRule.objects.all()
    serializer_class = IngredientRuleSerializer


class SubstitutionSuggestView(APIView):
    """Generate LLM substitution candidates and gate them through deterministic rules."""

    def post(self, request):
        start = time.perf_counter()
        serializer = SubstitutionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        ingredient = data["ingredient"]
        profile_key = data.get("profile_key", "default")
        recipe_title = ""
        if data.get("recipe_id"):
            recipe = Recipe.objects.filter(pk=data["recipe_id"]).first()
            if recipe:
                recipe_title = recipe.title

        profile, _ = UserDietaryProfile.objects.get_or_create(profile_key=profile_key)
        allergies = (
            data["allergies"] if "allergies" in data else (profile.allergies or [])
        )
        dietary_preferences = (
            data["dietary_preferences"]
            if "dietary_preferences" in data
            else (profile.dietary_preferences or [])
        )

        raw_candidates, provider_used = generate_substitution_candidates(
            ingredient=ingredient,
            recipe_title=recipe_title,
            allergies=allergies,
            dietary_preferences=dietary_preferences,
            inject_unsafe_candidates=data.get("inject_unsafe_candidates", []),
        )

        validator = DeterministicRuleValidator()
        outcome = validator.validate(
            ingredient_name=ingredient,
            candidates=raw_candidates,
            allergies=allergies,
            dietary_preferences=dietary_preferences,
        )

        latency_ms = round((time.perf_counter() - start) * 1000.0, 2)

        SubstitutionAuditLog.objects.create(
            requested_ingredient=ingredient,
            resolved_canonical=outcome.resolved_canonical or "",
            active_allergies=allergies,
            active_diets=dietary_preferences,
            provider_used=provider_used,
            raw_candidates=raw_candidates,
            accepted_candidates=outcome.accepted,
            rejected_candidates=outcome.rejected,
            final_status=outcome.status,
            latency_ms=latency_ms,
        )

        return Response(
            {
                "status": outcome.status,
                "ai_assisted": outcome.ai_assisted,
                "requested_ingredient": outcome.requested_ingredient,
                "resolved_canonical": outcome.resolved_canonical,
                "active_allergies": allergies,
                "active_dietary_preferences": dietary_preferences,
                "provider_used": provider_used,
                "suggestions": outcome.accepted,
                "rejected_candidates": outcome.rejected,
                "message": outcome.message,
                "limitations": outcome.limitations,
                "latency_ms": latency_ms,
            },
            status=status.HTTP_200_OK,
        )


@api_view(["GET"])
def health_check(request):
    """Health check endpoint verifying DB connectivity and deterministic rules readiness."""
    db_ok = True
    db_error = ""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as exc:
        db_ok = False
        db_error = str(exc)

    rules_count = IngredientRule.objects.count() if db_ok else 0
    recipes_count = Recipe.objects.count() if db_ok else 0

    healthy = db_ok and rules_count > 0
    payload = {
        "status": "healthy" if healthy else "degraded",
        "database": "connected" if db_ok else f"error: {db_error}",
        "database_vendor": connection.vendor,
        "rules_loaded": rules_count,
        "recipes_count": recipes_count,
        "llm_provider": getattr(settings, "LLM_PROVIDER", "mock"),
    }
    return Response(
        payload,
        status=status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
    )


@api_view(["GET"])
def metrics_view(request):
    """Operational metrics endpoint (JSON default, Prometheus text with ?output=prometheus)."""
    total_recipes = Recipe.objects.count()
    total_rules = IngredientRule.objects.count()
    logs = SubstitutionAuditLog.objects.all()
    total_requests = logs.count()
    verified_requests = logs.filter(final_status="verified").count()
    no_safe_requests = logs.filter(final_status="no_safe_suggestion").count()
    avg_latency = round(logs.aggregate(avg=Avg("latency_ms"))["avg"] or 0.0, 2)
    total_rejected_candidates = sum(len(log.rejected_candidates or []) for log in logs)

    metrics = {
        "reciperelay_recipes_total": total_recipes,
        "reciperelay_rules_total": total_rules,
        "reciperelay_substitution_requests_total": total_requests,
        "reciperelay_substitution_verified_total": verified_requests,
        "reciperelay_substitution_no_safe_total": no_safe_requests,
        "reciperelay_rejected_candidates_total": total_rejected_candidates,
        "reciperelay_substitution_avg_latency_ms": avg_latency,
    }

    if request.query_params.get("output") == "prometheus":
        lines = [f"{key} {val}" for key, val in metrics.items()]
        return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; version=0.0.4")

    return Response(metrics, status=status.HTTP_200_OK)
