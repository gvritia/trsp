"""Страницы просмотра существующих заказов доставки."""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from models.orders import get_order, get_order_status, sort_orders
from storage import load_delivery_data


def order_list(request: HttpRequest) -> HttpResponse:
    """Показать отсортированные заказы из JSON-хранилища."""
    _, _, orders, _ = load_delivery_data(settings.BASE_DIR / "data")
    context = {"orders": sort_orders(orders, key="id")}
    return render(request, "delivery_orders/order_list.html", context)


def order_detail(request: HttpRequest, order_id: int) -> HttpResponse:
    """Показать найденный заказ или шаблон с кодом HTTP 404."""
    _, _, orders, _ = load_delivery_data(settings.BASE_DIR / "data")
    try:
        order = get_order(orders, order_id)
    except ValueError:
        context = {
            "message": "Заказ не найден.",
            "back_url_name": "delivery_orders:list",
            "back_label": "К списку заказов",
        }
        return render(
            request, "homepage/not_found.html", context, status=404
        )

    context = {
        "order": order,
        "status_description": get_order_status(order),
    }
    return render(request, "delivery_orders/order_detail.html", context)
