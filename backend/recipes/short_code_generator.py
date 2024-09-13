import uuid

from django.conf import settings
from django.core.exceptions import ValidationError


def generate_short_code(model_class, field_name,
                        length=settings.SHORT_CODE_LENGTH):
    """Генератор уникальных кодов на основе UUID с проверкой уникальности."""

    if length < 1:
        raise ValidationError("Длина должна быть не менее 1.")

    while True:
        short_code = str(uuid.uuid4())[:length]
        # Проверка уникальности в базе данных
        if not model_class.objects.filter(**{field_name: short_code}).exists():
            return short_code
