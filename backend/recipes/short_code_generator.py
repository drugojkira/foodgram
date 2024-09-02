import random
import string

from django.conf import settings


def generate_short_code(length=settings.SHORT_CODE_LENGTH):
    """Генератор уникальных кодов"""
    from recipes.models import Recipe
    characters = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choice(characters) for _ in range(length))
        if not Recipe.objects.filter(short_url_code=code).exists():
            return code
