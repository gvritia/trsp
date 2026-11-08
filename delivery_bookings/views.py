"""Страницы поиска, создания и отмены бронирований через ORM."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from delivery_orders.models import Order
from .models import Booking
from .services import (
    BookingError,
    find_available_couriers,
    reserve_courier,
    valid_delivery_date,
)


def _booking_rows():
    bookings = Booking.objects.select_related(
        "order", "order__client", "courier"
    ).order_by("-delivery_date", "id")
    return [
        {
            "id": row.id,
            "order_id": row.order_id,
            "delivery_date": row.delivery_date,
            "is_cancelled": row.is_cancelled,
            "destination": row.order.destination,
            "client_name": row.order.client.name,
            "courier_name": row.courier.name,
        }
        for row in bookings
    ]


def _availability_context(request: HttpRequest, error: str = "") -> dict:
    values = request.GET if request.method == "GET" else request.POST
    raw_date = values.get("date", "")
    raw_order_id = values.get("order_id", "")
    orders = (
        Order.objects.filter(status=Order.STATUS_CREATED)
        .exclude(bookings__is_cancelled=False)
        .order_by("id")
    )
    selected_order = (
        orders.filter(pk=raw_order_id).first()
        if raw_order_id.isdigit()
        else None
    )
    if raw_order_id and selected_order is None and not error:
        error = "Выберите созданный заказ без действующего бронирования."
    couriers = None
    if raw_date:
        try:
            day = valid_delivery_date(raw_date)
            if not error:
                weight = selected_order.weight if selected_order else 0
                couriers = find_available_couriers(day, weight)
        except BookingError as exc:
            error = str(exc)
    return {
        "date": raw_date,
        "order_id": raw_order_id,
        "orders": orders,
        "selected_order": selected_order,
        "couriers": couriers,
        "error": error,
    }


def available_couriers(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "delivery_bookings/available.html",
        _availability_context(request),
    )


def booking_list(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "delivery_bookings/booking_list.html",
        {"bookings": _booking_rows()},
    )


@require_POST
def create_booking(request: HttpRequest) -> HttpResponse:
    try:
        reserve_courier(
            int(request.POST.get("order_id", "")),
            int(request.POST.get("courier_id", "")),
            valid_delivery_date(request.POST.get("date", "")),
        )
    except (ValueError, BookingError) as exc:
        error = (
            str(exc)
            if isinstance(exc, BookingError)
            else "Выберите заказ и курьера."
        )
        return render(
            request,
            "delivery_bookings/available.html",
            _availability_context(request, error),
            status=400,
        )
    return redirect("delivery_bookings:list")


@require_POST
def cancel(request: HttpRequest, booking_id: int) -> HttpResponse:
    booking = Booking.objects.filter(pk=booking_id, is_cancelled=False).first()
    if booking is None:
        return render(
            request,
            "delivery_bookings/booking_list.html",
            {
                "bookings": _booking_rows(),
                "error": "Действующее бронирование не найдено.",
            },
            status=404,
        )
    booking.cancel()
    return redirect("delivery_bookings:list")
