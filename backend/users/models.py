from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from users.constants import NAMES_MAX_LENGTH


class FoodgramUser(AbstractUser):
    """Модель пользователя."""

    first_name = models.CharField(_('first name'), max_length=NAMES_MAX_LENGTH)
    last_name = models.CharField(_('last name'), max_length=NAMES_MAX_LENGTH)
    email = models.EmailField(_('email address'), unique=True)
    avatar = models.ImageField(_('avatar'), upload_to='users', blank=True)

    REQUIRED_FIELDS = ('first_name', 'last_name', 'username')
    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def clean(self):
        """Валидация для поля username."""
        if not self.username.isalnum():
            raise ValidationError("Ник должен содержать только буквы и цифры.")

    def get_absolute_url(self):
        """Возвращает URL профиля пользователя."""
        return reverse('users:profile', kwargs={'pk': self.pk})


class UserSubscriptions(models.Model):
    """Промежуточная модель для подписок пользователя."""

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
        verbose_name_plural = 'Подписки'
