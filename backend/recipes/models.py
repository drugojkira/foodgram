from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from recipes.constants import (MAX_AMOUNT, MEASUREMENT_NAME_MAX_LENGTH,
                               MIN_AMOUNT, NAME_MAX_LENGTH,
                               SHORT_URL_CODE_MAX_LENGTH, TAG_NAME_MAX_LENGTH)
from recipes.short_code_generator import generate_short_code

User = get_user_model()


class Ingredient(models.Model):
    """Модель ингредиентов."""

    name = models.CharField("Название", max_length=NAME_MAX_LENGTH)
    measurement_unit = models.CharField(
        "Единица измерения",
        max_length=MEASUREMENT_NAME_MAX_LENGTH
    )

    class Meta:
        verbose_name = "ингредиент"
        verbose_name_plural = "Ингредиенты"
        default_related_name = "ingredients"
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=("name", "measurement_unit"),
                name="name_measurement_unit_unique"
            )
        ]

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Модель тегов."""

    name = models.CharField(
        "Название",
        max_length=TAG_NAME_MAX_LENGTH,
        unique=True
    )
    slug = models.SlugField("Слаг", unique=True)

    class Meta:
        verbose_name = "тег"
        verbose_name_plural = "Теги"
        default_related_name = "tags"
        ordering = ("name",)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецептов."""

    name = models.CharField("Название", max_length=NAME_MAX_LENGTH)
    image = models.ImageField("Картинка", upload_to="recipes/images")
    text = models.TextField("Описание")
    cooking_time = models.PositiveSmallIntegerField(
        "Время приготовления",
        validators=(
            MinValueValidator(1),
            MaxValueValidator(MAX_AMOUNT)
        )
    )
    created_at = models.DateTimeField("Время добавления", auto_now_add=True)
    short_url_code = models.CharField(
        "Набор символов для короткой ссылки",
        max_length=SHORT_URL_CODE_MAX_LENGTH
    )
    author = models.ForeignKey(
        User,
        verbose_name="Автор",
        on_delete=models.CASCADE,
        related_name="author_recipes"
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
        verbose_name="Ингредиенты",
        related_name="ingredients_recipes"
    )
    tags = models.ManyToManyField(
        Tag,
        through="RecipeTag",
        verbose_name="Теги",
        related_name="tags_recipes"
    )

    class Meta:
        verbose_name = "рецепт"
        verbose_name_plural = "Рецепты"
        default_related_name = "recipes"
        ordering = ("-created_at",)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.short_url_code:
            self.short_url_code = generate_short_code()
        return super().save(*args, **kwargs)


class RecipeTag(models.Model):
    """Промежуточная модель тегов и рецептов."""

    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Рецепт",
        on_delete=models.CASCADE
    )
    tag = models.ForeignKey(Tag, verbose_name="Тег", on_delete=models.CASCADE)

    class Meta:
        default_related_name = "recipetags"


class RecipeIngredient(models.Model):
    """Промежуточная модель ингредиентов и рецептов."""

    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Рецепт",
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient, verbose_name="Ингредиент", on_delete=models.CASCADE
    )
    amount = models.PositiveSmallIntegerField(
        "Количество", validators=(
            MinValueValidator(MIN_AMOUNT),
            MaxValueValidator(MAX_AMOUNT)
        )
    )

    class Meta:
        default_related_name = "recipeingredients"


class BaseUserList(models.Model):
    """Базовая модель для списков рецептов и пользователя."""

    user = models.ForeignKey(
        User,
        verbose_name="Пользователь",
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Рецепт",
        on_delete=models.CASCADE
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=("user", "recipe"),
                name="user_recipe_unique"
            )
        ]


class UserFavorite(BaseUserList):
    """Модель для списка избранного пользователя."""

    class Meta:
        verbose_name = "избранное"
        verbose_name_plural = "Избранные"


class UserShoppingList(BaseUserList):
    """Модель для списка покупок пользователя."""

    class Meta:
        verbose_name = "список покупок"
        verbose_name_plural = "Списки покупок"
