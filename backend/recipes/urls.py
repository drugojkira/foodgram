from django.urls import path, re_path
from django.conf import settings
from . import views

urlpatterns = [
    # Простой путь для расширения короткой ссылки
    path(
        f'{settings.SHORT_LINK_URL_PATH}/<str:uniq_id>/',
        views.expand, name='expand'
    ),

    # Альтернативный путь, если uniq_id может содержать не только буквы и цифры
    re_path(
        rf'^{settings.SHORT_LINK_URL_PATH}/(?P<uniq_id>[\w-]+)/$',
        views.expand, name='expand'
    ),
]
