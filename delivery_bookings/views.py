"""Формы поиска, создания, редактирования и отмены бронирований."""

from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from delivery_orders.models import Order
from .forms import BookingFilterForm, BookingForm
from .models import Booking
from .services import (
    BookingError,
    find_available_couriers,
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
    raw_date = request.GET.get("date", "")
    raw_order_id = request.GET.get("order_id", "")
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
                couriers = find_available_couriers(
                    day, selected_order.weight if selected_order else 0
                )
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
    form = BookingFilterForm(request.GET or None)
    bookings = _booking_queryset()
    sort = "-date"
    if form.is_valid():
        values = form.cleaned_data
        if values["status"]:
            bookings = bookings.filter(status=values["status"])
        if values["date"]:
            bookings = bookings.for_date(values["date"])
        if values["courier"]:
            bookings = bookings.filter(courier=values["courier"])
        if values["order"]:
            bookings = bookings.filter(order=values["order"])
        sort = values["sort"] or "-date"
    bookings = bookings.order_by(ORDERING[sort], "id")
    page = Paginator(bookings, PAGE_SIZE).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)
    return render(
        request,
        "delivery_bookings/booking_list.html",
        {
            "form": form,
            "bookings": page.object_list,
            "page_obj": page,
            "query_string": params.urlencode(),
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


def _render_booking_form(request, form, title, submit_label, status=200):
    return render(
        request,
        "delivery_bookings/booking_form.html",
        {
            "form": form,
            "page_title": title,
            "submit_label": submit_label,
        },
        status=status,
    )


def _create_post_data(request):
    """Принять прежние имена полей из формы подбора курьера."""
    data = request.POST.copy()
    for old, new in (
        ("order_id", "order"),
        ("courier_id", "courier"),
        ("date", "delivery_date"),
    ):
        if new not in data and old in data:
            data[new] = data[old]
    return data


@require_http_methods(["GET", "POST"])
def create_booking(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = BookingForm(_create_post_data(request))
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
            except IntegrityError:
                form.add_error(None, "Заказ или курьер уже забронирован.")
            else:
                return redirect("delivery_bookings:list")
        return _render_booking_form(
            request, form, "Новое бронирование", "Забронировать", status=400
        )
    form = BookingForm(
        initial={
            "order": request.GET.get("order_id", ""),
            "courier": request.GET.get("courier_id", ""),
            "delivery_date": request.GET.get("date", ""),
        }
    )
    return _render_booking_form(
        request, form, "Новое бронирование", "Забронировать"
    )


@require_http_methods(["GET", "POST"])
def edit_booking(request: HttpRequest, booking_id: int) -> HttpResponse:
    booking = get_object_or_404(Booking, pk=booking_id)
    if request.method == "POST":
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
            except IntegrityError:
                form.add_error(None, "Заказ или курьер уже забронирован.")
            else:
                return redirect(
                    "delivery_bookings:detail", booking_id=booking.pk
                )
        return _render_booking_form(
            request,
            form,
            f"Изменить бронирование #{booking.pk}",
            "Сохранить",
            status=400,
        )
    form = BookingForm(instance=booking)
    return _render_booking_form(
        request, form, f"Изменить бронирование #{booking.pk}", "Сохранить"
    )


@require_POST
def cancel(request: HttpRequest, booking_id: int) -> HttpResponse:
    booking = Booking.objects.active().filter(pk=booking_id).first()
    if booking is None:
        return render(
            request,
            "homepage/not_found.html",
            {
                "message": "Действующее бронирование не найдено.",
                "back_url_name": "delivery_bookings:list",
                "back_label": "К списку бронирований",
            },
            status=404,
        )
    booking.cancel()
    return redirect("delivery_bookings:list")
