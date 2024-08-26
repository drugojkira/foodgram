from django.db import models
from django.utils.translation import gettext_lazy as _

NAME_MAX_LENGHT = 150
TAG_NAME_MAX_LENGHT = 50
MEASUREMENT_NAME_MAX_LENGHT = 10
SHORT_URL_CODE_MAX_LENGTH = 6
MIN_AMOUNT = 1
MAX_AMOUNT = 32766


class MeasurementUnit(models.TextChoices):
    """Возможные единицы измерения."""

    ML = "мл", _("Миллилитр")
    G = "г", _("Грамм")
    TSP = "ч. л.", _("Чайная ложка")
    BSP = "ст. л.", _("Столовая ложка")
    PC = "шт.", _("Штука")
    DROP = "капля", _("Капля")
    PIECE = "кусок", _("Кусок")
    CAN = "банка", _("Банка")
    PINCH = "щепотка", _("Щепотка")
    HANDFUL = "горсть", _("Горсть")
    BATON = "батон", _("Батон")
    TWIG = "веточка", _("Веточка")
    GLASS = "стакан", _("Стакан")
