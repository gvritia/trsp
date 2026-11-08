"""Главная страница и фактическая статистика из Django ORM."""

from django.db.models import Avg, Count, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from delivery_bookings.models import Booking
from delivery_orders.models import Order
from delivery_routes.models import Route
from .models import Client, Courier


def index(request: HttpRequest) -> HttpResponse:
    active = Order.objects.filter(
        status__in=[Order.STATUS_CREATED, Order.STATUS_ASSIGNED]
    )
    active_count = active.count()
    return render(
        request,
        "homepage/index.html",
        {
            "client_count": Client.objects.count(),
            "courier_count": Courier.objects.count(),
            "order_count": Order.objects.count(),
            "route_count": Route.objects.count(),
            "efficiency": (
                100
                * active.filter(status=Order.STATUS_ASSIGNED).count()
                / active_count
                if active_count
                else 0
            ),
        },
    )


def statistics(request: HttpRequest) -> HttpResponse:
    booking_count = Booking.objects.count()
    active_bookings = Booking.objects.filter(is_cancelled=False).count()
    statuses = (
        Order.objects.values("status")
        .annotate(order_count=Count("id"), total_weight=Sum("weight"))
        .order_by("status")
    )
    workload = Courier.objects.annotate(
        order_count=Count(
            "orders", filter=Q(orders__status=Order.STATUS_ASSIGNED)
        ),
        total_weight=Coalesce(
            Sum("orders__weight", filter=Q(orders__status=Order.STATUS_ASSIGNED)),
            Value(0.0),
        ),
    ).order_by("id")
    busy = (
        Courier.objects.annotate(
            assigned_orders=Count(
                "orders", filter=Q(orders__status=Order.STATUS_ASSIGNED)
            )
        )
        .filter(assigned_orders__gt=0)
        .order_by("name")
    )
    bookings_by_courier = Courier.objects.annotate(
        booking_count=Count("bookings", filter=Q(bookings__is_cancelled=False))
    ).order_by("id")
    return render(
        request,
        "homepage/statistics.html",
        {
            "metrics": {
                "total_orders": Order.objects.count(),
                "average_weight": Order.objects.aggregate(value=Avg("weight"))[
                    "value"
                ]
                or 0,
            },
            "statuses": statuses,
            "workload": workload,
            "busy_couriers": busy,
            "clients": Client.objects.order_by("id"),
            "couriers": Courier.objects.order_by("id"),
            "booking_metrics": {
                "total_bookings": booking_count,
                "active_bookings": active_bookings,
            },
            "bookings_by_courier": [
                {"name": row.name, "booking_count": row.booking_count}
                for row in bookings_by_courier
            ],
        },
    )


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    return render(
        request,
        "homepage/not_found.html",
        {
            "message": "Такой страницы нет.",
            "back_url_name": "homepage:index",
            "back_label": "На главную",
        },
        status=404,
    )
