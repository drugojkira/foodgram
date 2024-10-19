from django.conf import settings
from django.urls import path

from . import views

urlpatterns = [
    # Основной маршрут для расширения короткой ссылки
    path(
        f'{settings.SHORT_LINK_URL_PATH}/<str:uniq_id>/',
        views.expand,
        name='expand'
    ),
    path('recipes/<int:pk>/', views.RecipeDetailView.as_view(), name='detail'),
]
