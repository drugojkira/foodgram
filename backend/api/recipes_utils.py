from datetime import datetime


def format_shopping_cart(ingredients, recipes):
    """
    Формирование строки для файла со списком покупок.
    Добавлены дата, нумерация продуктов, заголовки и список рецептов.
    """
    # Получение текущей даты
    current_date = datetime.now().strftime('%Y-%m-%d')

    # Проверка структуры входных данных
    if not ingredients or not recipes:
        return f"Список покупок пуст на {current_date}."

    # Заголовки и нумерация продуктов
    ingredients = [
        f"{index}. {item['ingredient__name'].capitalize()} – "
        f"{item['amount']} {item['ingredient__measurement_unit']}"
        for index, item in enumerate(ingredients, 1)
    ]

    # Перечень рецептов
    recipes = [f"- {recipe.name}" for recipe in recipes]

    # Составляем и возвращаем весь отчет
    return '\n'.join([
        f"Список покупок на {current_date}:",
        "Продукты:",
        *ingredients,
        "",
        "Рецепты:",
        *recipes
    ])
