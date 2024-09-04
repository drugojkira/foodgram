import uuid
from django.conf import settings


def generate_short_code(length=settings.SHORT_CODE_LENGTH):
    """Генератор уникальных кодов на основе UUID."""
    return str(uuid.uuid4())[:length]
