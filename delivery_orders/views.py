"""Страницы заказов; выборка, фильтрация и пагинация через ORM."""

from django.db.models import F, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from delivery_bookings.models import Booking
from .models import Order

STATUS_DESCRIPTIONS = {
    "создан": "Заказ ожидает назначения курьера",
    "назначен": "Курьер назначен",
    "отменён": "Заказ отменён",
    "доставлен": "Заказ доставлен",
}
PAGE_SIZE = 2


def order_list(request: HttpRequest) -> HttpResponse:
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    selected_status = (
        status if status in STATUS_DESCRIPTIONS or status == "активные" else ""
    )
    # F обращается к полям связанных таблиц; annotate добавляет эти значения
    # к объектам выборки без нового поля в модели или миграции.
    orders = (
        Order.objects.select_related("client", "courier")
        .annotate(
            client_name=F("client__name"),
            courier_name=F("courier__name"),
        )
        .order_by("id")
    )
    if query:
        orders = orders.filter(
            Q(destination__icontains=query)
            | Q(client__name__icontains=query)
            | Q(courier__name__icontains=query)
        )
    if status == "активные":
        orders = orders.filter(
            status__in=[Order.STATUS_CREATED, Order.STATUS_ASSIGNED]
        )
    elif status in STATUS_DESCRIPTIONS:
        orders = orders.filter(status=status)
    total_orders = orders.count()
    total_pages = max(1, (total_orders + PAGE_SIZE - 1) // PAGE_SIZE)
    try:
        page = int(request.GET.get("page", "1"))
    except ValueError:
        page = 1
    page = min(max(page, 1), total_pages)
    if not query and not selected_status:
        orders = orders[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]
    rows = [
        {
            "id": order.id,
            "destination": order.destination,
            "weight": order.weight,
            "status": order.status,
            # Имена получены из annotate и передаются в шаблон через context.
            "client_name": order.client_name,
            "courier_name": order.courier_name,
        }
        for order in orders
    ]
    return render(
        request,
        "delivery_orders/order_list.html",
        {
            "orders": rows,
            "query": query,
            "selected_status": selected_status,
            "statuses": STATUS_DESCRIPTIONS,
            "total_orders": total_orders,
            "page": page,
            "total_pages": total_pages,
            "previous_page": page - 1 if page > 1 else None,
            "next_page": page + 1 if page < total_pages else None,
            "is_paginated": not query and not selected_status,
        },
    )


def order_detail(request: HttpRequest, order_id: int) -> HttpResponse:
    order = (
        Order.objects.select_related("client", "courier")
        .filter(pk=order_id)
        .first()
    )
    if order is None:
        return render(
            request,
            "homepage/not_found.html",
            {
                "message": "Заказ не найден.",
                "back_url_name": "delivery_orders:list",
                "back_label": "К списку заказов",
            },
            status=404,
        )
    booking = (
        Booking.objects.select_related("courier")
        .active().filter(order=order)
        .first()
    )
    return render(
        request,
        "delivery_orders/order_detail.html",
        {
            "order": {
                "id": order.id,
                "destination": order.destination,
                "weight": order.weight,
                "status": order.status,
                "client_name": order.client.name,
                "courier_name": order.courier.name if order.courier else None,
            },
            "status_description": STATUS_DESCRIPTIONS[order.status],
            "booking": (
                {
                    "courier_name": booking.courier.name,
                    "delivery_date": booking.delivery_date,
                }
                if booking
                else None
            ),
        },
    )
