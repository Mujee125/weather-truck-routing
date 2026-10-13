from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("healthcheck.urls")),
    path("api/", include("trip_analysis.api.urls")),
]