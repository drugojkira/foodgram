from datetime import datetime


def format_shopping_cart(ingredients, recipes):
    """
    Формирование строки для файла со списком покупок.
    Добавлены дата, нумерация продуктов, заголовки и список рецептов.
    """

    # Заголовки и нумерация продуктов
    ingredients = [
        f"{index + 1}. {item['ingredient__name'].capitalize()} – "
        f"{item['amount']} {item['ingredient__measurement_unit']}"
        for index, item in enumerate(ingredients)
    ]

    # Перечень рецептов
    recipes = [f"- {recipe.name}" for recipe in recipes]

    # Составляем и возвращаем весь отчет
    return '\n'.join([
        f"Список покупок на {datetime.now().strftime('%Y-%m-%d')}:",
        "Продукты:",
        *ingredients,
        "\nРецепты:",
        *recipes
    ])
