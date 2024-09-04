from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from users.models import UserSubscriptions  # Подписки пользователей
from recipes.models import Recipe  # Рецепты пользователей

User = get_user_model()


class HasRecipesFilter(admin.SimpleListFilter):
    """Фильтр для пользователей, у которых есть рецепты."""
    title = 'с рецептами'
    parameter_name = 'has_recipes'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'С рецептами'),
            ('no', 'Без рецептов'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(author_recipes__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(author_recipes__isnull=True)


class HasSubscriptionsFilter(admin.SimpleListFilter):
    """Фильтр для пользователей с подписками."""
    title = 'с подписками'
    parameter_name = 'has_subscriptions'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'С подписками'),
            ('no', 'Без подписок'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(subscriptions__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(subscriptions__isnull=True)


class HasSubscribersFilter(admin.SimpleListFilter):
    """Фильтр для пользователей, на которых подписаны другие."""
    title = 'с подписчиками'
    parameter_name = 'has_subscribers'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'С подписчиками'),
            ('no', 'Без подписчиков'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(subscribed_to__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(subscribed_to__isnull=True)


class FoodgramUserAdmin(UserAdmin):
    """Отображение пользователей с дополнительными полями и фильтрами."""

    search_fields = ("username", "email")
    list_display = (
        "username", "email", "avatar_image", "recipe_count",
        "subscription_count", "subscriber_count"
    )
    list_filter = (
        HasRecipesFilter, HasSubscriptionsFilter, HasSubscribersFilter
    )

    @admin.display(description="Аватар")
    def avatar_image(self, user):
        """Отображение аватара пользователя в виде картинки."""
        if user.avatar:
            return format_html(
                '<img src="{}" style="width: 50px; height:50px;" />',
                user.avatar.url
            )
        return "Нет аватара"

    @admin.display(description="Рецепты")
    def recipe_count(self, user):
        """Количество рецептов пользователя."""
        return Recipe.objects.filter(author=user).count()

    @admin.display(description="Подписки")
    def subscription_count(self, user):
        """Количество подписок пользователя."""
        return UserSubscriptions.objects.filter(user=user).count()

    @admin.display(description="Подписчики")
    def subscriber_count(self, user):
        """Количество подписчиков пользователя."""
        return UserSubscriptions.objects.filter(subscription=user).count()


admin.site.register(User, FoodgramUserAdmin)
admin.site.unregister(Group)
