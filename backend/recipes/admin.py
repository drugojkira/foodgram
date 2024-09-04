from django.contrib import admin
from django.utils.safestring import mark_safe
from recipes.models import (Ingredient, Recipe, RecipeIngredient, RecipeTag,
                            Tag, UserFavorite)


class TagAdmin(admin.ModelAdmin):
    """Отображение тегов."""

    search_fields = ("name",)


class IngredientAdmin(admin.ModelAdmin):
    """Отображение ингредиентов с фильтром по единицам измерения и тегам."""

    search_fields = ("name", "tags__name")  # Поиск по имени и тегам
    list_display = ("name", "measurement_unit")  # Отображение единиц измерения
    list_filter = ("measurement_unit",)  # Фильтр по единицам измерения


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

    list_display = ("name", "author", "created_at", "count_favorites")
    readonly_fields = ("created_at", "short_url_code", "count_favorites")
    inlines = (RecipeIngredientInline, RecipeTagInline)

    search_fields = (
        "name",
        "author__username",
        "author__first_name",
        "author__last_name",
        "tags__name",
    )

    # Фильтр по авторам и времени готовки
    list_filter = ("tags__name", "author", "cooking_time")

    # Пример фильтра по времени готовки с кастомизированными подписями
    def get_cooking_time_range(self):
        """Фильтр по времени готовки."""
        return [
            ("fast", "Быстрее 30 мин"),
            ("medium", "Быстрее 60 мин"),
            ("long", "Дольше 60 мин"),
        ]

    fields = (
        "name",
        "text",
        "image",
        "created_at",
        "short_url_code",
        "author",
        "cooking_time",
        "count_favorites",  # Отображение числа избранных
        "display_tags",  # Отображение тегов
        "display_ingredients",  # Отображение ингредиентов
    )

    # Отображение тегов (в столбик)
    @admin.display(description="Теги")
    def display_tags(self, recipe):
        return mark_safe("<br>".join([tag.name for tag in recipe.tags.all()]))

    # Отображение ингредиентов (в столбик: имя, ед.изм., мера)
    @admin.display(description="Ингредиенты")
    def display_ingredients(self, recipe):
        ingredients_list = [
            f"{ingredient.ingredient.name} "
            f"({ingredient.ingredient.measurement_unit}) — {ingredient.amount}"
            for ingredient in recipe.recipeingredient_set.all()
        ]
        return mark_safe("<br>".join(ingredients_list))

    @admin.display(description="Избранные")
    def count_favorites(self, recipe):
        return recipe.userfavorite.count()


# Админ управление для всех моделей
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(UserFavorite)
admin.site.register(RecipeIngredient)
admin.site.register(RecipeTag)
