"""Маршруты страниц доставки."""

from django.urls import path

from . import views

# Имена ниже используются в шаблонах через {% url 'delivery_routes:...' %}.
app_name = "delivery_routes"

urlpatterns = [
    path("", views.route_list, name="list"),
    # route_id поступает в параметр одноимённой view-функции.
    path("<int:route_id>/", views.route_detail, name="detail"),
    # Не-число не подходит под int: показываем отдельное сообщение об ошибке.
    path("<str:route_id>/", views.invalid_route_id, name="invalid_id"),
]
