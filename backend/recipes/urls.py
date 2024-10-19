from django.urls import path

from . import views

app_name = 'recipes'

urlpatterns = [
    # Маршрут для короткой ссылки
    path('s/<str:uniq_id>/', views.expand, name='expand'),
    # Маршрут для детального просмотра рецепта
    path('recipes/<int:pk>/', views.RecipeDetailView.as_view(), name='detail'),
]
