"""Главная страница и общий обработчик неизвестных URL."""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from models.orders import calculate_efficiency
from storage import load_delivery_data


def index(request: HttpRequest) -> HttpResponse:
    """Показать показатели на основе существующих JSON-данных."""
    # Загрузка восстанавливает связи Order → Client/Courier и Route → Order.
    clients, couriers, orders, routes = load_delivery_data(
        settings.BASE_DIR / "data"
    )
    # View вычисляет данные, а шаблон решает, как вывести их в HTML.
    context = {
        "client_count": len(clients),
        "courier_count": len(couriers),
        "order_count": len(orders),
        "route_count": len(routes),
        "efficiency": calculate_efficiency(orders),
    }
    return render(request, "homepage/index.html", context)


def page_not_found(
    request: HttpRequest, exception: Exception
) -> HttpResponse:
    """Отобразить общую страницу 404 для неизвестного URL."""
    # Имя маршрута передаётся в шаблон для кнопки возврата через {% url %}.
    context = {
        "message": "Такой страницы нет.",
        "back_url_name": "homepage:index",
        "back_label": "На главную",
    }
    return render(request, "homepage/not_found.html", context, status=404)
