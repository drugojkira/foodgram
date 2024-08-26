from django.conf import settings
from django.urls import path

from recipes import views

urlpatterns = [
    path(f'{settings.SHORT_LINK_URL_PATH}/<str:uniq_id>/', views.expand),
]
