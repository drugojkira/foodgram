from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from djoser.serializers import UserCreateSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.constants import MIN_AMOUNT
from recipes.models import (Ingredient, Recipe, RecipeIngredient, Tag,
                            UserFavorite, UserShoppingList, UserSubscriptions)
from rest_framework import serializers

User = get_user_model()


class UserSerializer(DjoserUserSerializer):
    """
    Модифицированный сериализатор пользователя, добавляющий поле is_subscribed.
    """

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = DjoserUserSerializer.Meta.fields + (
            "is_subscribed",
            "avatar",
        )

    def get_is_subscribed(self, user):
        """
        Проверяем, подписан ли текущий пользователь на данного пользователя.
        """
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return UserSubscriptions.objects.filter(
            user=request.user, author=user
        ).exists()


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для изменения аватара пользователя."""

    avatar = Base64ImageField(required=False)

    class Meta:
        model = User
        fields = ("avatar",)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = "__all__"


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = "__all__"


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецептах."""

    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = RecipeIngredient
        fields = ("amount", "id", "name", "measurement_unit")


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для получения и изменения рецептов."""

    author = UserSerializer()
    tags = TagSerializer(many=True)
    ingredients = RecipeIngredientSerializer(
        many=True, source="recipeingredients"
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id", "tags", "author", "ingredients", "name", "image", "text",
            "cooking_time", "is_favorited", "is_in_shopping_cart"
        )

    def get_is_favorited(self, recipe):
        """Проверяем, есть ли рецепт в избранном пользователя."""
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return UserFavorite.objects.filter(
            user=request.user,
            recipe=recipe
        ).exists()

    def get_is_in_shopping_cart(self, recipe):
        """Проверяем, есть ли рецепт в списке покупок пользователя."""
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return UserShoppingList.objects.filter(
            user=request.user,
            recipe=recipe
        ).exists()


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания ингредиентов в рецептах."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ("amount", "id")


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""

    image = Base64ImageField()
    ingredients = RecipeIngredientCreateSerializer(
        many=True, source="recipeingredients"
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )

    class Meta:
        model = Recipe
        fields = (
            "id",
            "ingredients",
            "tags",
            "image",
            "name",
            "text",
            "cooking_time",
        )

    def validate_image(self, value):
        """Проверка загружаемого изображения."""
        if not value:
            raise ValidationError("Необходимо загрузить изображение.")
        if not value.name.lower().endswith(('.jpg', '.jpeg', '.png')):
            raise ValidationError(
                "Файл должен быть изображением формата JPEG или PNG."
            )
        if value.size > 5 * 1024 * 1024:
            raise ValidationError(
                "Размер изображения не должен превышать 5 MB."
            )
        return value

    @staticmethod
    def validate_ingredients(ingredients):
        """Проверка на наличие повторяющихся ингредиентов."""
        ingredient_ids = [ingredient['id'] for ingredient in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            duplicated_ingredients = [
                ingredient['id'] for ingredient in ingredients
                if ingredient_ids.count(ingredient['id']) > 1
            ]
            raise ValidationError(
                f"Ингредиенты не должны повторяться. Повторяющиеся: "
                f"{set(duplicated_ingredients)}."
            )
        return ingredients

    @staticmethod
    def validate_tags(tags):
        """Проверка на уникальность тегов."""
        if len(tags) != len(set(tags)):
            duplicated_tags = [tag for tag in tags if tags.count(tag) > 1]
            raise ValidationError(
                f"Теги не должны повторяться. Повторяющиеся: "
                f"{set(duplicated_tags)}."
            )
        return tags

    @staticmethod
    def validate_ingredient_amounts(ingredients):
        """Проверка на корректные значения количества ингредиентов."""
        invalid_ingredients = [
            (
                ingredient['id'], ingredient['amount']
            ) for ingredient in ingredients
            if ingredient['amount'] < MIN_AMOUNT
        ]
        if invalid_ingredients:
            invalid_details = [
                f"ID: {ingredient_id}, Amount: {amount}"
                for ingredient_id, amount in invalid_ingredients
            ]
            raise ValidationError(
                f"Количество следующих ингредиентов должно быть больше или "
                f"равно {MIN_AMOUNT}: {invalid_details}."
            )
        return ingredients

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop("recipeingredients", [])
        tags = validated_data.pop("tags")
        image = validated_data.pop("image", None)

        # Создание рецепта с изображением
        recipe = Recipe.objects.create(
            **validated_data, author=self.context["request"].user, image=image
        )
        recipe.tags.set(tags)
        self.add_ingredients_to_recipe(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop("recipeingredients", [])
        tags = validated_data.pop("tags")
        image = validated_data.pop("image", None)

        instance.tags.clear()
        instance.tags.set(tags)
        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.add_ingredients_to_recipe(instance, ingredients)

        # Обновление изображения
        if image:
            instance.image = image

        return super().update(instance, validated_data)

    @staticmethod
    def add_ingredients_to_recipe(recipe, ingredients):
        """Добавление ингредиентов к рецепту с валидацией значений."""
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                ingredient=ingredient["id"], amount=ingredient["amount"],
                recipe=recipe
            ) for ingredient in ingredients
        )


class SubscriptionsSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения подписок пользователя."""

    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source="author.recipes.count", read_only=True
    )
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = UserSubscriptions
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "recipes",
            "recipes_count",
            "is_subscribed",
        )

    def get_recipes(self, subscription):
        """
        Получаем рецепты автора, на которого подписан пользователь.
        """
        # Получаем ограничение на количество рецептов, если указано
        recipes_limit = self.context["request"].query_params.get(
            "recipes_limit"
        )
        try:
            recipes_limit = int(recipes_limit)
        except (TypeError, ValueError):
            recipes_limit = None

        # Получаем рецепты автора (subscription.author)
        recipes = subscription.author.recipes.all()
        if recipes_limit:
            recipes = recipes[:recipes_limit]

        # Сериализуем и возвращаем рецепты автора
        return RecipeSerializer(recipes, many=True, context=self.context).data

    def get_is_subscribed(self, subscription):
        """
        Проверяем, подписан ли текущий пользователь на автора.
        """
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False

        # Проверка наличия подписки на автора
        return UserSubscriptions.objects.filter(
            user=request.user, author=subscription.author
        ).exists()
