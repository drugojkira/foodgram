from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from recipes.models import Recipe


def expand(request, uniq_id):
    """Представление для коротких ссылок."""
    recipe = get_object_or_404(Recipe, short_url_code=uniq_id)
    return redirect(reverse('recipes-detail', kwargs={'pk': recipe.id}))
