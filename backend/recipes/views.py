from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404

from recipes.models import Recipe


def expand(request, uniq_id):
    """Представление для коротких ссылок."""
    try:
        recipe = get_object_or_404(Recipe, short_url_code=uniq_id)
        return HttpResponseRedirect(
            request.build_absolute_uri(f"/recipes/{recipe.id}/")
        )
    except Exception as e:
        return HttpResponse(e.args)
