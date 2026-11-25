"""DRF serializers for RecipeRelay."""

from rest_framework import serializers
from .models import (
    IngredientRule,
    Recipe,
    RecipeIngredient,
    UserDietaryProfile,
    normalize_ingredient_name,
)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Serializer for structured recipe ingredients."""

    class Meta:
        model = RecipeIngredient
        fields = ["id", "name", "normalized_name", "quantity", "unit", "notes"]
        read_only_fields = ["id", "normalized_name"]


class RecipeSerializer(serializers.ModelSerializer):
    """Serializer for Recipe CRUD with nested ingredients."""

    ingredients = RecipeIngredientSerializer(many=True)
    share_path = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            "id",
            "title",
            "slug",
            "author_name",
            "description",
            "instructions",
            "prep_time_minutes",
            "servings",
            "dietary_tags",
            "is_public",
            "share_token",
            "share_path",
            "ingredients",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "share_token", "share_path", "created_at", "updated_at"]

    def get_share_path(self, obj: Recipe) -> str:
        return f"/?share={obj.share_token}"

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError("At least one ingredient is required.")
        return value

    def validate_dietary_tags(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("dietary_tags must be a list of strings.")
        return [str(tag).strip().lower() for tag in value if str(tag).strip()]

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        for ing in ingredients_data:
            RecipeIngredient.objects.create(recipe=recipe, **ing)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("ingredients", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        if ingredients_data is not None:
            instance.ingredients.all().delete()
            for ing in ingredients_data:
                RecipeIngredient.objects.create(recipe=instance, **ing)
        return instance


class UserDietaryProfileSerializer(serializers.ModelSerializer):
    """Serializer for user allergy exclusions and dietary preferences."""

    class Meta:
        model = UserDietaryProfile
        fields = ["profile_key", "allergies", "dietary_preferences", "updated_at"]
        read_only_fields = ["updated_at"]

    def validate_allergies(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("allergies must be a list.")
        return [normalize_ingredient_name(str(item)) for item in value if str(item).strip()]

    def validate_dietary_preferences(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("dietary_preferences must be a list.")
        return [normalize_ingredient_name(str(item)) for item in value if str(item).strip()]


class IngredientRuleSerializer(serializers.ModelSerializer):
    """Read-only serializer for inspecting deterministic ingredient rules."""

    class Meta:
        model = IngredientRule
        fields = [
            "id",
            "canonical_name",
            "aliases",
            "allergens",
            "dietary_incompatible",
            "allowed_substitutes",
            "is_ambiguous",
            "ambiguity_reason",
            "notes",
        ]


class SubstitutionRequestSerializer(serializers.Serializer):
    """Input validator for ingredient substitution requests."""

    ingredient = serializers.CharField(max_length=140)
    recipe_id = serializers.UUIDField(required=False, allow_null=True)
    profile_key = serializers.CharField(max_length=80, required=False, default="default")
    allergies = serializers.ListField(
        child=serializers.CharField(max_length=60), required=False
    )
    dietary_preferences = serializers.ListField(
        child=serializers.CharField(max_length=60), required=False
    )
    inject_unsafe_candidates = serializers.ListField(
        child=serializers.CharField(max_length=140), required=False, default=list
    )
