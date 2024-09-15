import json

from django.core.management.base import BaseCommand
from recipes.models import Ingredient, Tag


class Command(BaseCommand):
    help = (
        "Загрузка данных из JSON-файлов в модели. ",
        "Пример команды: python manage.py import_data ",
    )

    def handle(self, *args, **options):
        # Импорт данных из JSON-файлов
        self.import_data_from_json('data/ingredients.json', Ingredient)
        self.import_data_from_json('data/tags.json', Tag)

    def import_data_from_json(self, json_file_path, model):
        """Импорт данных из JSON-файла в модель """
        with open(json_file_path, 'r', encoding='utf-8') as json_file:
            data_list = json.load(json_file)

        # Используем bulk_create для ускорения процесса
        objects = [model(**data) for data in data_list]
        model.objects.bulk_create(objects)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully imported data for {model}")
        )
