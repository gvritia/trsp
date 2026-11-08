"""Корневая маршрутизация веб-интерфейса доставки."""

from django.contrib import admin
from django.conf import settings
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # include передаёт оставшуюся часть URL в urls.py выбранного приложения.
    path("", include("homepage.urls")),
    # ПР7, 7.6 №15 и №25: /orders/ передаётся в delivery_orders/urls.py.
    # Часть ?status=создан не участвует в выборе URL; она попадёт в request.GET.
    path("orders/", include("delivery_orders.urls")),
    path("routes/", include("delivery_routes.urls")),
    path("bookings/", include("delivery_bookings.urls")),
]

# Django вызывает этот обработчик для неизвестных URL при DEBUG=False.
handler404 = "homepage.views.page_not_found"

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += debug_toolbar_urls()
