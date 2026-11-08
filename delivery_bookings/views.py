"""Поиск, фильтрация и управление бронированиями через Django ORM."""

from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from delivery_orders.models import Order
from homepage.models import Courier
from .models import Booking
from .services import (
    BookingError,
    find_available_couriers,
    reserve_courier,
    valid_delivery_date,
)

PAGE_SIZE = 5
ORDERING = {
    "date": "delivery_date",
    "-date": "-delivery_date",
    "id": "id",
    "-id": "-id",
}


def _booking_queryset():
    return Booking.objects.select_related("order", "order__client", "courier")


def _availability_context(request: HttpRequest, error: str = "") -> dict:
    values = request.GET if request.method == "GET" else request.POST
    raw_date = values.get("date", "")
    raw_order_id = values.get("order_id", "")
    orders = (
        Order.objects.filter(status=Order.STATUS_CREATED)
        .exclude(pk__in=Booking.objects.active().values("order_id"))
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
    bookings = _booking_queryset()
    status = request.GET.get("status", "")
    raw_date = request.GET.get("date", "")
    raw_courier = request.GET.get("courier", "")
    raw_order = request.GET.get("order", "")
    sort = request.GET.get("sort", "-date")
    if status in Booking.Status.values:
        bookings = bookings.filter(status=status)
    else:
        status = ""
    if raw_date:
        try:
            bookings = bookings.for_date(valid_delivery_date(raw_date))
        except BookingError:
            bookings = bookings.none()
    if raw_courier.isdigit():
        bookings = bookings.filter(courier_id=raw_courier)
    if raw_order.isdigit():
        bookings = bookings.filter(order_id=raw_order)
    sort = sort if sort in ORDERING else "-date"
    bookings = bookings.order_by(ORDERING[sort], "id")
    page = Paginator(bookings, PAGE_SIZE).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(
        request,
        "delivery_bookings/booking_list.html",
        {
            "bookings": page.object_list,
            "page_obj": page,
            "query_string": params.urlencode(),
            "selected_status": status,
            "selected_date": raw_date,
            "selected_courier": raw_courier,
            "selected_order": raw_order,
            "selected_sort": sort,
            "statuses": Booking.Status.choices,
            "couriers": Courier.objects.order_by("name"),
            "orders": Order.objects.order_by("id"),
        },
    )


def booking_detail(request: HttpRequest, booking_id: int) -> HttpResponse:
    booking = _booking_queryset().filter(pk=booking_id).first()
    if booking is None:
        return render(
            request,
            "homepage/not_found.html",
            {
                "message": "Бронирование не найдено.",
                "back_url_name": "delivery_bookings:list",
                "back_label": "К списку бронирований",
            },
            status=404,
        )
    return render(
        request, "delivery_bookings/booking_detail.html", {"booking": booking}
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
    booking = Booking.objects.active().filter(pk=booking_id).first()
    if booking is None:
        return render(
            request,
            "delivery_bookings/booking_list.html",
            {
                "bookings": _booking_queryset().order_by(
                    "-delivery_date", "id"
                ),
                "error": "Действующее бронирование не найдено.",
            },
            status=404,
        )
    booking.cancel()
    return redirect("delivery_bookings:list")
