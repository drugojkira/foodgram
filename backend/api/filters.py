from django_filters import rest_framework as filters
from django_filters.filters import CharFilter, ModelMultipleChoiceFilter
from django_filters.rest_framework import BooleanFilter
from rest_framework.filters import SearchFilter

from recipes.models import Recipe, Tag


class IngredientSearchFilter(SearchFilter):
    """Фильтр для ингредиентов рецепта."""

    search_param = "name"


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов."""

    author = CharFilter(field_name="author")
    tags = ModelMultipleChoiceFilter(
        field_name="tags__slug",
        queryset=Tag.objects.all(),
        to_field_name="slug",
        conjoined=False,
    )
    is_favorited = BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = BooleanFilter(method="filter_is_in_shopping_cart")

    def filter_is_favorited(self, recipes_queryset, name, value):
        if self.request.user.is_authenticated and value:
            return recipes_queryset.filter(
                userfavorite__user=self.request.user
            )
        return recipes_queryset

    def filter_is_in_shopping_cart(self, recipes_queryset, name, value):
        if self.request.user.is_authenticated and value:
            return recipes_queryset.filter(
                usershoppinglist__user=self.request.user
            )
        return recipes_queryset

    class Meta:
        model = Recipe
        fields = ("author", "tags", "is_favorited", "is_in_shopping_cart")
