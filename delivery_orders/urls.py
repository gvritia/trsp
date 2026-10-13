"""Маршруты страниц заказов."""

from django.urls import path

from . import views

# Имена ниже используются в шаблонах через {% url 'delivery_orders:...' %}.
app_name = "delivery_orders"

urlpatterns = [
    path("", views.order_list, name="list"),
    # int преобразует часть URL в число и передаёт его в order_detail.
    path("<int:order_id>/", views.order_detail, name="detail"),
]
