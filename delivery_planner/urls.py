"""Корневая маршрутизация веб-интерфейса доставки."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # include передаёт оставшуюся часть URL в urls.py выбранного приложения.
    path("", include("homepage.urls")),
    path("orders/", include("delivery_orders.urls")),
    path("routes/", include("delivery_routes.urls")),
]

# Django вызывает этот обработчик для неизвестных URL при DEBUG=False.
handler404 = "homepage.views.page_not_found"
