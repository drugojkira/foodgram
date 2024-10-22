from django.db.models import Q
from django_filters import rest_framework as filters
from django_filters.filters import CharFilter, ModelMultipleChoiceFilter
from django_filters.rest_framework import BooleanFilter
from recipes.models import Recipe, Tag
from rest_framework.filters import BaseFilterBackend


class IngredientSearchFilter(BaseFilterBackend):
    """Кастомный фильтр для поиска ингредиентов"""

    search_param = 'name'

    def filter_queryset(self, request, queryset, view):
        search_term = request.query_params.get(self.search_param, '').strip()
        if search_term:
            if search_term.isdigit():
                # Если введена цифра, ищем по содержимому
                return queryset.filter(Q(name__icontains=search_term))
            else:
                # Если введена буква, ищем по первой букве без учета регистра
                return queryset.filter(
                    Q(name__istartswith=search_term.lower())
                )
        return queryset


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов."""

    author = CharFilter(field_name="author__id")
    tags = ModelMultipleChoiceFilter(
        field_name="tags__slug",
        queryset=Tag.objects.all(),
        to_field_name="slug",
        conjoined=False,
    )
    is_favorited = BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = BooleanFilter(method="filter_is_in_shopping_cart")

    def filter_is_favorited(self, recipes, name, value):
        if self.request.user.is_authenticated and value:
            return recipes.filter(
                userfavorites__user=self.request.user
            )
        return recipes

    def filter_is_in_shopping_cart(self, recipes, name, value):
        if self.request.user.is_authenticated and value:
            return recipes.filter(
                usershoppinglists__user=self.request.user
            )
        return recipes

    class Meta:
        model = Recipe
        fields = (
            "author",
            "tags",
            "is_favorited",
            "is_in_shopping_cart",
        )
