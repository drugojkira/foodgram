from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import F, Q
from recipes.constants import (MEASUREMENT_NAME_MAX_LENGTH, MIN_AMOUNT,
                               NAME_MAX_LENGTH, SHORT_URL_CODE_MAX_LENGTH,
                               TAG_NAME_MAX_LENGTH)
from recipes.short_code_generator import generate_short_code

USERNAME_REGEX = r'^[a-zA-Z0-9._]+$'


class FoodgramUser(AbstractUser):
    """Модель пользователя."""

    username = models.CharField(
        'Имя пользователя',
        max_length=NAME_MAX_LENGTH,
        unique=True,
        validators=[RegexValidator(
            regex=USERNAME_REGEX,
            message="Имя пользователя может содержать только "
                    "буквы, цифры и символы."
        )]
    )
    first_name = models.CharField('Имя', max_length=NAME_MAX_LENGTH)
    last_name = models.CharField('Фамилия', max_length=NAME_MAX_LENGTH)
    email = models.EmailField('Электронная почта', unique=True)
    avatar = models.ImageField('Аватар', upload_to='users', blank=True)
    subscriptions = models.ManyToManyField(
        'self', symmetrical=False, related_name='subscribers', blank=True
    )

    REQUIRED_FIELDS = ('first_name', 'last_name', 'username')
    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'
        ordering = ('username', )


class Ingredient(models.Model):
    """Модель ингредиентов."""

    name = models.CharField('Название', max_length=NAME_MAX_LENGTH)
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=MEASUREMENT_NAME_MAX_LENGTH
    )

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        default_related_name = 'ingredients'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='name_measurement_unit_unique'
            )
        ]

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Модель тегов."""

    name = models.CharField(
        'Название',
        max_length=TAG_NAME_MAX_LENGTH,
        unique=True
    )
    slug = models.SlugField('Слаг', unique=True)

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'
        default_related_name = 'tags'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецептов."""

    name = models.CharField('Название', max_length=NAME_MAX_LENGTH)
    image = models.ImageField('Картинка', upload_to='recipes/images')
    text = models.TextField('Описание')
    cooking_time = models.PositiveIntegerField(
        'Время приготовления',
        validators=[
            MinValueValidator(1)
        ]
    )
    created_at = models.DateTimeField('Время добавления', auto_now_add=True)
    short_url_code = models.CharField(
        'Код короткой ссылки',
        max_length=SHORT_URL_CODE_MAX_LENGTH
    )
    author = models.ForeignKey(
        FoodgramUser,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
        related_name='recipes'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        related_name='recipes'
    )

    user_favorites = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='favorite_recipes',
        blank=True
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at',)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.short_url_code:
            self.short_url_code = generate_short_code(
                self.__class__, 'short_url_code'
            )
        return super().save(*args, **kwargs)


class RecipeIngredient(models.Model):
    """Промежуточная модель ингредиентов и рецептов."""

    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='recipeingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient, verbose_name='Ингредиент', on_delete=models.CASCADE
    )
    amount = models.PositiveIntegerField(
        'Количество', validators=[
            MinValueValidator(MIN_AMOUNT)
        ]
    )

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'
        default_related_name = 'recipeingredients'


class BaseUserRecipeList(models.Model):
    """Базовая модель для списков рецептов пользователя."""

    user = models.ForeignKey(
        FoodgramUser,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='%(class)ss'
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='%(class)ss'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='%(class)s_user_recipe_unique'
            )
        ]


class UserFavorite(BaseUserRecipeList):
    """Модель для списка избранного пользователя."""

    class Meta(BaseUserRecipeList.Meta):
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранные'


class UserShoppingList(BaseUserRecipeList):
    """Модель для списка покупок пользователя."""

    class Meta(BaseUserRecipeList.Meta):
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'


class UserSubscriptions(models.Model):
    """Модель для подписок пользователя."""

    user = models.ForeignKey(
        FoodgramUser,
        verbose_name='Пользователь',
        related_name='followers',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        FoodgramUser,
        verbose_name='Автор',
        related_name='authors',
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'), name='unique_subscription'
            ),
            models.CheckConstraint(
                check=~Q(user=F('author')),
                name='prevent_self_subscription'
            )
        ]
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'
