from django.db import models

NAME_MAX_LENGTH = 150
TAG_NAME_MAX_LENGTH = 50
MEASUREMENT_NAME_MAX_LENGTH = 10
SHORT_URL_CODE_MAX_LENGTH = 6
MIN_AMOUNT = 1


class MeasurementUnit(models.Model):
    """Модель для хранения единиц измерения."""

    name = models.CharField(max_length=MEASUREMENT_NAME_MAX_LENGTH)

    def __str__(self):
        return self.name
