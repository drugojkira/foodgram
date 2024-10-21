from django.urls import path

from . import views

app_name = 'recipes'

urlpatterns = [
    # Маршрут для короткой ссылки
    path('s/<str:uniq_id>/', views.expand, name='expand'),
    # Обычный маршрут для рецепта
    path('recipes/<int:pk>/', views.expand, name='detail'),
]
