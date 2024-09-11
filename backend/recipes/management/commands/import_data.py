import csv
import json
import os
import shutil

from django.apps import apps
from django.core.management.base import BaseCommand
from recipes.models import Ingredient, Tag

triples = [
    "recipes:Ingredient:data/ingredients.csv",
    "recipes:Tag:data/tags.csv",
    "users:FoodgramUser:data/users.csv",
    "recipes:Recipe:data/recipes.csv",
    "recipes:RecipeTag:data/recipetag.csv",
    "recipes:RecipeIngredient:data/recipeingredient.csv",
]

# Пути для копирования изображений
avatar_src_file = "data/default_avatar.png"
recipe_src_file = "data/default_recipe_image.png"
avatar_dest_directory = "media/users"
recipe_dest_directory = "media/recipes/images"


class Command(BaseCommand):
    help = (
        "Загрузка данных из csv- и json-файлов в модели. ",
        "Пример команды: python manage.py import_data ",
    )

    def handle(self, *args, **options):
        # Копируем файлы с изображениями
        self.copy_file(avatar_src_file, avatar_dest_directory)
        self.copy_file(recipe_src_file, recipe_dest_directory)

        # Импорт данных из CSV
        for triple in triples:
            parts = triple.split(":")
            if len(parts) == 3:
                app_name, model_name, csv_file_path = parts
                model = apps.get_model(app_name, model_name)
                self.import_data_from_csv(model, csv_file_path)
            else:
                self.stdout.write(
                    self.style.ERROR(f"Неверный формат: '{triple}'")
                )

        # Импорт данных из JSON-файлов
        self.import_data_from_json('data/ingredients.json', Ingredient)
        self.import_data_from_json('data/tags.json', Tag)

    def copy_file(self, src_file, dest_dir):
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        dest_path = os.path.join(dest_dir, os.path.basename(src_file))
        shutil.copy2(src_file, dest_path)
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully copied {src_file} to {dest_path}"
            )
        )

    def import_data_from_csv(self, model, csv_file_path):
        """Импорт данных из CSV-файла в модель."""
        with open(csv_file_path, newline="", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            field_names = next(reader)  # Получение заголовков
            for row in reader:
                data = {
                    field_names[i]: row[i] for i in range(len(field_names))
                }
                # Распаковываем словарь и создаем объект модели
                model.objects.create(**data)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully imported data for {model}")
        )

    def import_data_from_json(self, json_file_path, model):
        """Импорт данных из JSON-файла в модель."""
        with open(json_file_path, 'r', encoding='utf-8') as json_file:
            data_list = json.load(json_file)

        for data in data_list:
            model.objects.create(**data)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully imported data for {model}")
        )
