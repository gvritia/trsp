"""Маршруты и связанные заказы из Django ORM."""

from django.db.models import Count, Prefetch
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from delivery_orders.models import Order
from .models import Route


def _route_courier(route):
    orders = list(route.orders.all())
    return (
        orders[0].courier.name
        if orders and orders[0].courier
        else "Не назначен"
    )


def _route_queryset():
    return Route.objects.prefetch_related(
        Prefetch(
            "orders",
            queryset=Order.objects.select_related("courier").order_by("id"),
        )
    )


def route_list(request: HttpRequest) -> HttpResponse:
    routes = (
        _route_queryset().annotate(order_count=Count("orders")).order_by("id")
    )
    rows = [
        {
            "id": route.id,
            "status": route.status,
            "url": route.get_absolute_url(),
            "courier_name": _route_courier(route),
            "order_count": route.order_count,
        }
        for route in routes
    ]
    return render(request, "delivery_routes/route_list.html", {"routes": rows})


def route_detail(request: HttpRequest, route_id: int) -> HttpResponse:
    route = _route_queryset().filter(pk=route_id).first()
    if route is None:
        return render(
            request,
            "homepage/not_found.html",
            {
                "page_title": "Маршрут не найден",
                "message": f"Маршрут с ID {route_id} не найден.",
                "back_url_name": "delivery_routes:list",
                "back_label": "К списку маршрутов",
            },
            status=404,
        )
    return _render_route_detail(request, route)


def slug_detail(request: HttpRequest, slug: str) -> HttpResponse:
    route = _route_queryset().filter(slug=slug).first()
    if route is None:
        return render(
            request,
            "homepage/not_found.html",
            {
                "page_title": "Маршрут не найден",
                "message": f"Маршрут «{slug}» не найден.",
                "back_url_name": "delivery_routes:list",
                "back_label": "К списку маршрутов",
            },
            status=404,
        )
    return _render_route_detail(request, route)


def _render_route_detail(request: HttpRequest, route: Route) -> HttpResponse:
    return render(
        request,
        "delivery_routes/route_detail.html",
        {
            "route": {
                "id": route.id,
                "status": route.status,
                "courier_name": _route_courier(route),
                "orders": route.orders.all(),
            }
        },
    )


def invalid_route_id(request: HttpRequest, route_id: str) -> HttpResponse:
    return render(
        request,
        "homepage/not_found.html",
        {
            "page_title": "Некорректный ID маршрута",
            "message": "ID маршрута должен быть целым неотрицательным числом.",
            "back_url_name": "delivery_routes:list",
            "back_label": "К списку маршрутов",
        },
        status=404,
    )
