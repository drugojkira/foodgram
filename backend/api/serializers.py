from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Ingredient, Recipe, RecipeIngredient, Tag,
                            UserFavorite, UserShoppingList)
from users.models import UserSubscriptions

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователей."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "is_subscribed",
        )

    def get_is_subscribed(self, obj):
        """Проверяем, подписан ли текущий пользователь"""
        request = self.context.get("request")
        return (
            request
            and request.user.is_authenticated
            and UserSubscriptions.objects.filter(
                user=request.user, subscription=obj
            ).exists()
        )


class AvatarSerializer(serializers.ModelSerializer):

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ("avatar",)

    def validate_avatar(self, value):
        if value is None:
            raise ValidationError("Передано пустое поле avatar")
        return value


class IngredientSerialiser(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = "__all__"


class TagSerialiser(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = "__all__"


class RecipeIngredientGetSerializer(serializers.ModelSerializer):
    """Получение данных"""

    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = RecipeIngredient
        fields = ("amount", "id", "name", "measurement_unit")


class RecipeGetSerialiser(serializers.ModelSerializer):

    image = Base64ImageField()
    author = UserSerializer()
    tags = TagSerialiser(many=True)
    ingredients = RecipeIngredientGetSerializer(
        many=True,
        source="recipeingredient"
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
            "is_favorited",
            "is_in_shopping_cart",
        )

    def get_is_favorited(self, obj):
        """Проверяем, есть ли рецепт в избранном пользователя."""
        request = self.context.get("request")
        return (
            request
            and request.user.is_authenticated
            and UserFavorite.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """Проверяем, есть ли рецепт в списке покупок пользователя."""
        request = self.context.get("request")
        return (
            request
            and request.user.is_authenticated
            and UserShoppingList.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        )


class RecipeFavoriteGetSerialiser(serializers.ModelSerializer):

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class RecipeIngredientPostSerialiser(serializers.ModelSerializer):

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
    )

    class Meta:
        model = RecipeIngredient
        fields = ("amount", "id")


class RecipePostSerialiser(serializers.ModelSerializer):

    image = Base64ImageField()
    ingredients = RecipeIngredientPostSerialiser(
        many=True,
        source="recipeingredient"
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )

    class Meta:
        model = Recipe
        fields = (
            "ingredients",
            "tags",
            "image",
            "name",
            "text",
            "cooking_time"
        )

    def validate(self, data):
        """Добавляем проверку на наличие полей для метода PATCH."""
        request_method = self.context["request"].method
        if request_method == "PATCH":
            required_fields = (
                "recipeingredient",
                "tags",
                "name",
                "text",
                "cooking_time",
            )
            for field in required_fields:
                if field not in data:
                    raise serializers.ValidationError(
                        {field: f"{field} является обязательным"}
                    )
        return data

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                "Картинка обязательно должна быть добавлена"
            )
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                "Необходимо указать хотя бы один тег."
            )
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Теги не должны повторяться.")
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                "Необходимо указать хотя бы один ингредиент."
            )
        ingredients_id_list = [ingredient["id"] for ingredient in value]
        if len(ingredients_id_list) != len(set(ingredients_id_list)):
            raise serializers.ValidationError(
                "Ингредиенты не должны повторяться."
            )
        return value

    @staticmethod
    def add_ingredients_to_recipeingredient(recipe, ingredients):
        """
        Метод для добавления ингредиентов к рецептам в промежуточную модель.
        """
        RecipeIngredient.objects.bulk_create(
            [
                RecipeIngredient(
                    ingredient=ingredient["id"],
                    amount=ingredient["amount"],
                    recipe=recipe,
                )
                for ingredient in ingredients
            ]
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop("recipeingredient")
        tags = validated_data.pop("tags")
        recipe = Recipe.objects.create(
            **validated_data, author=self.context.get("request").user
        )
        recipe.tags.set(tags)
        self.add_ingredients_to_recipeingredient(
            recipe=recipe,
            ingredients=ingredients
        )
        return recipe

    def update(self, instance, validated_data):
        new_tags = validated_data.pop("tags")
        new_ingredients = validated_data.pop("recipeingredient")

        instance.tags.clear()
        instance.tags.set(new_tags)

        instance.ingredients.clear()
        self.add_ingredients_to_recipeingredient(
            recipe=instance,
            ingredients=new_ingredients
        )
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeGetSerialiser(instance, context=self.context).data


class SubscriptionsRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class SubscriptionsPostSerializer(UserSerializer):
    """Для добавления подписок."""


class SubscriptionsSerializer(UserSerializer):
    """
    Для получение информации о пользователе,
    на которого текущий пользователь подписался.
    """

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def get_recipes(self, obj):
        """Получаем рецепты пользователя."""
        recipes_limit = self.context.get("request").query_params.get(
            "recipes_limit", None
        )
        recipes = obj.author_recipes.all()
        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
                if recipes_limit < 1:
                    raise serializers.ValidationError(
                        "Значение recipes_limit должно быть > 0"
                    )
                recipes = recipes[:recipes_limit]
            except ValueError:
                raise serializers.ValidationError(
                    "Значение recipes_limit не является числом"
                )
        serializer = SubscriptionsRecipeSerializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.author_recipes.count()


class UserSubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserSubscriptions
        fields = "__all__"
        validators = [
            UniqueTogetherValidator(
                queryset=UserSubscriptions.objects.all(),
                fields=("user", "subscription"),
            )
        ]

    def validate(self, attrs):
        if attrs["user"] == attrs["subscription"]:
            raise serializers.ValidationError(
                "Нельзя подписаться на самого себя"
            )
        return super().validate(attrs)

    def to_representation(self, instance):
        return SubscriptionsSerializer(
            instance.subscription,
            context=self.context
        ).data


class RecipeToFavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserFavorite
        fields = "__all__"
        validators = [
            UniqueTogetherValidator(
                queryset=UserFavorite.objects.all(), fields=("user", "recipe")
            )
        ]

    def to_representation(self, instance):
        return RecipeFavoriteGetSerialiser(instance.recipe).data


class RecipeToShoppingListSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserShoppingList
        fields = "__all__"
        validators = [
            UniqueTogetherValidator(
                queryset=UserShoppingList.objects.all(),
                fields=("user", "recipe")
            )
        ]

    def to_representation(self, instance):
        return RecipeFavoriteGetSerialiser(instance.recipe).data
