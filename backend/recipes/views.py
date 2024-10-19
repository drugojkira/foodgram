from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView
from recipes.models import Recipe


def expand(request, uniq_id):
    """Представление для коротких ссылок."""
    recipe = get_object_or_404(Recipe, short_url_code=uniq_id)
    return redirect('recipes:detail', pk=recipe.id)


class RecipeDetailView(DetailView):
    """Представление для отображения детальной страницы рецепта."""
    model = Recipe
    template_name = 'recipes/detail.html'
    context_object_name = 'recipe'
