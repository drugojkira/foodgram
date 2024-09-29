from django.shortcuts import get_object_or_404, redirect
from recipes.models import Recipe


def expand(request, uniq_id):
    """Представление для коротких ссылок."""
    recipe = get_object_or_404(Recipe, short_url_code=uniq_id)
    return redirect('recipes:detail', pk=recipe.id)
