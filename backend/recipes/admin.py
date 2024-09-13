from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe
from recipes.models import (
    Ingredient, Recipe, RecipeIngredient, RecipeTag, Tag, UserFavorite
)

User = get_user_model()


class CookingTimeFilter(admin.SimpleListFilter):
    """Фильтр по времени готовки."""
    title = "Время готовки"
    parameter_name = "cooking_time"

    def lookups(self, request, model_admin):
        return [
            ('fast', "Быстрее 30 мин"),
            ('medium', "Быстрее 60 мин"),
            ('long', "Дольше 60 мин"),
        ]

    def queryset(self, request, queryset):
        # Объединяем фильтры через использование `range`
        if self.value() == 'fast':
            return queryset.filter(cooking_time__lt=30)
        if self.value() == 'medium':
            return queryset.filter(cooking_time__range=(30, 60))
        if self.value() == 'long':
            return queryset.filter(cooking_time__gt=60)
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
            author_recipes__isnull=not has_recipes
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
            subscribed_to__isnull=not has_subscribers
        ).distinct()


class TagAdmin(admin.ModelAdmin):
    """Отображение тегов."""
    search_fields = ("name",)
    # Добавлено явно отображаемое поле для количества применений
    list_display = ("name", "slug", "recipes_count")

    def recipes_count(self, tag):
        """Количество рецептов, использующих данный тег."""
        return tag.tags_recipes.count()


class IngredientAdmin(admin.ModelAdmin):
    """Отображение ингредиентов с фильтром по единицам измерения и тегам."""
    search_fields = ("name", "tags__name")
    list_display = ("name", "measurement_unit", "recipes_count")
    list_filter = ("measurement_unit",)  # Фильтр по единицам измерения

    def recipes_count(self, ingredient):
        """Количество рецептов, использующих данный ингредиент."""
        return ingredient.ingredients_recipes.count()


class RecipeIngredientInline(admin.TabularInline):
    """Отображение ингредиентов рецепта."""
    model = RecipeIngredient
    extra = 1


class RecipeTagInline(admin.TabularInline):
    """Отображение тегов рецепта."""
    model = RecipeTag
    extra = 1


class RecipeAdmin(admin.ModelAdmin):
    """Отображение рецептов с фильтрацией и кастомизированными полями."""
    list_display = (
        "name",
        "author",
        "created_at",
        "count_favorites",
        "display_image"
    )
    readonly_fields = (
        "created_at",
        "short_url_code",
        "count_favorites",
        "display_image"
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
        "count_favorites",  # Отображение числа избранных
        "display_tags",  # Отображение тегов
        "display_ingredients",  # Отображение ингредиентов
    )

    @admin.display(description="Изображение")
    def display_image(self, recipe):
        """Отображение картинки в админке."""
        if recipe.image:
            return mark_safe(
                f'<img src="{recipe.image.url}" width="150" height="150" />'
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
        "subscriber_count"
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


admin.site.register(User, FoodgramUserAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(UserFavorite)
admin.site.register(RecipeIngredient)
