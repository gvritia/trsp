"""Маршруты страниц доставки."""

from django.urls import path

from . import views

# Имена ниже используются в шаблонах через {% url 'delivery_routes:...' %}.
app_name = "delivery_routes"

urlpatterns = [
    # ПР7, чек-лист 7.2 №24, №27: список маршрутов из SQLite.
    path("", views.route_list, name="list"),
    # route_id поступает в параметр одноимённой view-функции.
    path("<int:route_id>/", views.route_detail, name="detail"),
    path("by-slug/<slug:slug>/", views.slug_detail, name="slug_detail"),
    # Не-число не подходит под int: показываем отдельное сообщение об ошибке.
    path("<str:route_id>/", views.invalid_route_id, name="invalid_id"),
]
