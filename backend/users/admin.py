from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

User = get_user_model()


class FoodgramUserAdmin(UserAdmin):
    """Отображение пользователей."""

    search_fields = ("username", "email")


admin.site.register(User, FoodgramUserAdmin)
admin.site.unregister(Group)
