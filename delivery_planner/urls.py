"""Корневая маршрутизация веб-интерфейса доставки."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("homepage.urls")),
    path("orders/", include("delivery_orders.urls")),
    path("routes/", include("delivery_routes.urls")),
]

handler404 = "homepage.views.page_not_found"
