"""API URL routes for the recipes app."""

from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health_check, name="health-check"),
    path("metrics/", views.metrics_view, name="metrics"),
    path("recipes/", views.RecipeListCreateView.as_view(), name="recipe-list-create"),
    path("recipes/share/<str:share_token>/", views.RecipeShareView.as_view(), name="recipe-share"),
    path("recipes/<uuid:pk>/", views.RecipeDetailView.as_view(), name="recipe-detail"),
    path("preferences/", views.DietaryProfileView.as_view(), name="dietary-preferences"),
    path("rules/", views.IngredientRuleListView.as_view(), name="ingredient-rules"),
    path("substitutions/suggest/", views.SubstitutionSuggestView.as_view(), name="substitution-suggest"),
]
