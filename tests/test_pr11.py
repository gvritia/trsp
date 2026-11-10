"""Создание, редактирование, фильтрация и отмена через Django Forms."""

from datetime import timedelta

from django.test import Client as WebClient
from django.urls import reverse
from django.utils import timezone

from delivery_bookings.forms import BookingFilterForm, BookingForm
from delivery_bookings.models import Booking
from delivery_bookings.services import find_available_couriers
from delivery_orders.models import Order
from homepage.models import Client, Courier


def sample_objects():
    client = Client.objects.create(name="Клиент ПР11", phone="+7")
    courier = Courier.objects.create(name="Курьер ПР11", capacity=70)
    first = Order.objects.create(
        client=client, destination="Первый адрес ПР11", weight=60,
        status=Order.STATUS_CREATED,
    )
    second = Order.objects.create(
        client=client, destination="Второй адрес ПР11", weight=67,
        status=Order.STATUS_CREATED,
    )
    return first, second, courier


def future_day(days):
    return (timezone.localdate() + timedelta(days=days)).isoformat()


def booking_data(order, courier, day):
    return {
        "order": order.pk, "courier": courier.pk, "delivery_date": day,
    }


def test_create_form_validates_date_and_conflicts(rollback_orm):
    first, second, courier = sample_objects()
    browser = WebClient(HTTP_HOST="localhost")
    create_url = reverse("delivery_bookings:create")
    day = future_day(30)
    initial_count = Booking.objects.count()

    initial = browser.get(create_url, {
        "order_id": first.pk, "courier_id": courier.pk, "date": day,
    })
    assert initial.status_code == 200
    assert "Новое бронирование" in initial.content.decode("utf-8")

    missing = browser.post(create_url, {})
    assert missing.status_code == 400
    assert "Выберите заказ" in missing.content.decode("utf-8")
    assert Booking.objects.count() == initial_count

    invalid_date = browser.post(
        create_url, booking_data(first, courier, future_day(-1))
    )
    assert invalid_date.status_code == 400
    assert "прошедшую дату" in invalid_date.content.decode("utf-8")
    assert Booking.objects.count() == initial_count

    invalid_order = browser.post(create_url, {
        "order": 999999, "courier": courier.pk, "delivery_date": day,
    })
    assert invalid_order.status_code == 400
    assert Booking.objects.count() == initial_count

    assert browser.post(
        create_url, booking_data(first, courier, day)
    ).status_code == 302
    booking = Booking.objects.active().get(order=first)
    assert booking.delivery_date.isoformat() == day

    conflict = browser.post(create_url, booking_data(second, courier, day))
    conflict_html = conflict.content.decode("utf-8")
    assert conflict.status_code == 400
    assert "Курьер уже занят" in conflict_html
    assert day in conflict_html
    assert Booking.objects.count() == initial_count + 1


def test_edit_form_excludes_itself_and_preserves_record(rollback_orm):
    first, second, courier = sample_objects()
    browser = WebClient(HTTP_HOST="localhost")
    day = future_day(31)
    later = future_day(32)
    initial_count = Booking.objects.count()
    booking = Booking.objects.create(
        order=first, courier=courier, delivery_date=day
    )
    edit_url = reverse("delivery_bookings:edit", args=[booking.pk])

    assert browser.get(edit_url).status_code == 200
    assert browser.post(
        edit_url, booking_data(first, courier, day)
    ).status_code == 302
    assert Booking.objects.count() == initial_count + 1
    assert Booking.objects.get(pk=booking.pk).order == first

    assert browser.post(
        edit_url, booking_data(second, courier, later)
    ).status_code == 302
    booking.refresh_from_db()
    assert booking.order == second
    assert booking.delivery_date.isoformat() == later
    assert Booking.objects.count() == initial_count + 1
    missing = reverse("delivery_bookings:edit", args=[999999])
    assert browser.get(missing).status_code == 404


def test_filter_form_and_post_protection(rollback_orm):
    first, second, courier = sample_objects()
    browser = WebClient(HTTP_HOST="localhost")
    day = future_day(33)
    initial_count = Booking.objects.count()
    booking = Booking.objects.create(
        order=first, courier=courier, delivery_date=day
    )
    assert BookingFilterForm({"date": "not-a-date"}).is_valid() is False
    invalid_filter = browser.get("/bookings/", {"date": "not-a-date"})
    assert invalid_filter.status_code == 200
    assert "text-danger" in invalid_filter.content.decode("utf-8")
    assert Booking.objects.count() == initial_count + 1

    valid_filter = browser.get("/bookings/", {
        "status": "active", "date": day, "courier": courier.pk,
        "order": first.pk, "sort": "date",
    })
    assert valid_filter.status_code == 200
    assert first.destination in valid_filter.content.decode("utf-8")

    cancel_url = reverse("delivery_bookings:cancel", args=[booking.pk])
    assert browser.get(cancel_url).status_code == 405
    assert Booking.objects.active().filter(pk=booking.pk).exists()
    csrf_browser = WebClient(HTTP_HOST="localhost", enforce_csrf_checks=True)
    assert csrf_browser.post(cancel_url).status_code == 403
    assert csrf_browser.post(
        reverse("delivery_bookings:create"), booking_data(second, courier, day)
    ).status_code == 403
    assert csrf_browser.post(
        reverse("delivery_bookings:edit", args=[booking.pk]),
        booking_data(first, courier, day),
    ).status_code == 403
    assert browser.post(cancel_url).status_code == 302
    booking.refresh_from_db()
    assert booking.status == Booking.Status.CANCELLED
    assert courier in find_available_couriers(booking.delivery_date, 60)


def test_form_errors_keep_submitted_values(rollback_orm):
    first, _, _ = sample_objects()
    small_courier = Courier.objects.create(name="Малый курьер ПР11", capacity=10)
    form = BookingForm(booking_data(first, small_courier, future_day(34)))
    assert form.is_valid() is False
    assert "грузоподъёмности" in str(form.errors)
    assert str(form["order"].value()) == str(first.pk)
    assert str(form["courier"].value()) == str(small_courier.pk)
