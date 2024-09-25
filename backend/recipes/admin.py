from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe
from recipes.models import (FoodgramUser, Ingredient, Recipe, RecipeIngredient,
                            Tag, UserFavorite)

from .constants import (FAST_COOKING_TIME, LONG_COOKING_TIME,
                        MEDIUM_COOKING_TIME, TIME_FAST, TIME_MEDIUM)

User = get_user_model()


class CookingTimeFilter(admin.SimpleListFilter):
    """Фильтр по времени готовки."""
    title = "Время готовки"
    parameter_name = "cooking_time"

    def lookups(self, request, model_admin):
        return [
            (FAST_COOKING_TIME, f"Быстрее {TIME_FAST} мин"),
            (MEDIUM_COOKING_TIME, f"Быстрее {TIME_MEDIUM} мин"),
            (LONG_COOKING_TIME, f"Дольше {TIME_MEDIUM} мин"),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            min_time, max_time = eval(value)
            return queryset.filter(cooking_time__range=(min_time, max_time))
        return queryset


class HasRecipesFilter(admin.SimpleListFilter):
    """Фильтр для пользователей, у которых есть рецепты."""
    title = 'с рецептами'
    parameter_name = 'has_recipes'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'С рецептами'),
            ('no', 'Без рецептов'),
        )

    def queryset(self, request, queryset):
        has_recipes = self.value() == 'yes'
        return queryset.filter(
            recipes__isnull=not has_recipes
        ).distinct()


class HasSubscriptionsFilter(admin.SimpleListFilter):
    """Фильтр для пользователей с подписками."""
    title = 'с подписками'
    parameter_name = 'has_subscriptions'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'С подписками'),
            ('no', 'Без подписок'),
        )

    def queryset(self, request, queryset):
        has_subscriptions = self.value() == 'yes'
        return queryset.filter(
            subscriptions__isnull=not has_subscriptions
        ).distinct()


class HasSubscribersFilter(admin.SimpleListFilter):
    """Фильтр для пользователей, на которых подписаны другие."""
    title = 'с подписчиками'
    parameter_name = 'has_subscribers'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'С подписчиками'),
            ('no', 'Без подписчиков'),
        )

    def queryset(self, request, queryset):
        has_subscribers = self.value() == 'yes'
        return queryset.filter(
            subscriptions__isnull=not has_subscribers
        ).distinct()


class TagAdmin(admin.ModelAdmin):
    """Отображение тегов."""
    search_fields = ("name",)
    list_display = ("name", "slug", "recipes_count")

    def recipes_count(self, tag):
        """Количество рецептов, использующих данный тег."""
        return tag.recipes.count()


class IngredientAdmin(admin.ModelAdmin):
    """Отображение ингредиентов с фильтром по единицам измерения."""
    search_fields = ("name",)
    list_display = ("name", "measurement_unit", "recipes_count")
    list_filter = ("measurement_unit",)

    def recipes_count(self, ingredient):
        """Количество рецептов, использующих данный ингредиент."""
        return ingredient.recipes.count()


class RecipeIngredientInline(admin.TabularInline):
    """Отображение ингредиентов рецепта."""
    model = RecipeIngredient
    extra = 1


class RecipeTagInline(admin.TabularInline):
    """Отображение тегов рецепта."""
    model = Recipe.tags.through
    extra = 1


class RecipeAdmin(admin.ModelAdmin):
    """Отображение рецептов с фильтрацией и кастомизированными полями."""
    list_display = (
        "name",
        "author",
        "created_at",
        "count_favorites",
        "display_image",
    )
    readonly_fields = (
        "created_at",
        "short_url_code",
        "count_favorites",
        "display_image",
        "display_tags",
        "display_ingredients",
    )
    inlines = (RecipeIngredientInline, RecipeTagInline)
    search_fields = (
        "name",
        "author__username",
        "author__first_name",
        "author__last_name",
        "tags__name",
    )
    list_filter = ("tags__name", "author", CookingTimeFilter)

    fields = (
        "name",
        "image",
        "created_at",
        "short_url_code",
        "author",
        "cooking_time",
        "count_favorites",
        "display_image",
    )

    @admin.display(description='Изображение')
    def display_image(self, recipe):
        """Отображение картинки в админке."""
        if recipe.image:
            return mark_safe(
                f'<img src="{recipe.image.url}" '
                f'width="150" height="150" />'
            )
        return "Изображение отсутствует"

    @admin.display(description="Теги")
    def display_tags(self, recipe):
        return mark_safe("<br>".join(tag.name for tag in recipe.tags.all()))

    @admin.display(description="Ингредиенты")
    def display_ingredients(self, recipe):
        return mark_safe(
            "<br>".join(
                f"{ingredient.ingredient.name} "
                f"({ingredient.ingredient.measurement_unit}) — "
                f"{ingredient.amount}"
                for ingredient in recipe.recipeingredients.all()
            )
        )

    @admin.display(description="Избранные")
    def count_favorites(self, recipe):
        return recipe.user_favorites.count()


class FoodgramUserAdmin(UserAdmin):
    """Отображение пользователей с дополнительными полями и фильтрами."""

    search_fields = ("username", "email")
    list_display = (
        "username",
        "email",
        "avatar_image",
        "recipe_count",
        "subscription_count",
        "subscriber_count",
    )
    list_filter = (
        HasRecipesFilter, HasSubscriptionsFilter, HasSubscribersFilter
    )

    @admin.display(description="Аватар")
    def avatar_image(self, user):
        """Отображение аватара пользователя в виде картинки."""
        if user.avatar:
            return mark_safe(
                f'<img src="{user.avatar.url}" '
                f'style="width: 50px; height:50px;" />'
            )
        return "Нет аватара"

    @admin.display(description="Рецепты")
    def recipe_count(self, user):
        """Количество рецептов пользователя."""
        return user.recipes.count()

    @admin.display(description="Подписки")
    def subscription_count(self, user):
        """Количество подписок пользователя."""
        return user.followers.count()

    @admin.display(description="Подписчики")
    def subscriber_count(self, user):
        """Количество подписчиков пользователя."""
        return user.authors.count()


admin.site.register(FoodgramUser, FoodgramUserAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(UserFavorite)
admin.site.register(RecipeIngredient)
