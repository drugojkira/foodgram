from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("api/", include("api.urls")),
    path("admin/", admin.site.urls),
    path("", include("recipes.urls", namespace='recipes')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
