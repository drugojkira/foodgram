from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from recipes.models import Recipe


def expand(request, uniq_id):
    """Представление для коротких ссылок."""
    # Пытаемся найти рецепт по его id
    recipe = get_object_or_404(Recipe, id=uniq_id)

    # Перенаправляем на детальную страницу рецепта
    return redirect(reverse('api:recipes-detail', kwargs={'pk': recipe.id}))
