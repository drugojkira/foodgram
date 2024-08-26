from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from users.constants import NAMES_MAX_LENGTH


class FoodgramUser(AbstractUser):
    """Модель пользователя."""

    # Делаем поля модели обязательными
    first_name = models.CharField(_("first name"), max_length=NAMES_MAX_LENGTH)
    last_name = models.CharField(_("last name"), max_length=NAMES_MAX_LENGTH)
    email = models.EmailField(_("email address"), unique=True)
    avatar = models.ImageField(_("avatar"), upload_to="users", blank=True)
    subscriptions = models.ManyToManyField(
        "self",
        through="UserSubscriptions",
        verbose_name="Подписки",
        related_name="user",
        symmetrical=False
    )

    REQUIRED_FIELDS = ("first_name", "last_name", "username")
    USERNAME_FIELD = "email"

    class Meta:
        ordering = ("username",)

    def get_absolute_url(self):
        return reverse("users:profile")


class UserSubscriptions(models.Model):
    """Промежуточная модель для подписок пользователя."""

    user = models.ForeignKey(
        FoodgramUser,
        verbose_name="Пользователь",
        related_name='followers',
        on_delete=models.CASCADE
    )
    subscription = models.ForeignKey(
        FoodgramUser,
        verbose_name="Подписка",
        related_name='followings',
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "subscription"), name="Unique subscription"
            ),
            models.CheckConstraint(
                check=~Q(user=F('subscription')),
                name='prevent_self_subscription'
            )
        ]

    def clean(self):
        """Проверяем, что пользователь не подписывается сам на себя."""
        if self.user == self.subscription:
            raise ValidationError("Нельзя подписаться на самого себя.")
