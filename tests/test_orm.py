"""Проверки связей и правил предметной области после перехода на ORM."""

from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from delivery_bookings.models import Booking
from delivery_bookings.services import (
    BookingError, find_available_couriers, reserve_courier,
)
from delivery_orders.models import Order
from delivery_routes.models import Route, RouteOrder
from homepage.models import Client, Courier


def test_related_objects_and_route_validation(rollback_orm):
    client = Client.objects.create(name="Тестовый клиент", phone="+7")
    courier = Courier.objects.create(name="Тестовый курьер", capacity=10)
    other = Courier.objects.create(name="Другой курьер", capacity=10)
    first = Order.objects.create(
        client=client, courier=courier, destination="Адрес 1",
        weight=2, status=Order.STATUS_ASSIGNED,
    )
    second = Order.objects.create(
        client=client, courier=other, destination="Адрес 2",
        weight=2, status=Order.STATUS_ASSIGNED,
    )
    route = Route.objects.create()
    RouteOrder.objects.create(route=route, order=first)
    assert list(route.orders.all()) == [first]
    assert list(client.orders.filter(pk=first.pk)) == [first]
    assert first.route_link.route == route
    with pytest.raises(ValidationError):
        RouteOrder.objects.create(route=route, order=second)
    first.courier = other
    with pytest.raises(ValidationError):
        first.save()


def test_booking_cancellation_releases_courier(rollback_orm):
    day = date(2027, 1, 10)
    courier = Courier.objects.get(pk=3)
    assert courier in find_available_couriers(day, 60)
    booking = reserve_courier(3, courier.pk, day)
    assert Booking.objects.get(pk=booking.pk).order.client.name == "Елена Волкова"
    assert courier not in find_available_couriers(day, 60)
    with pytest.raises(BookingError):
        reserve_courier(4, courier.pk, day)
    with transaction.atomic():
        with pytest.raises(IntegrityError):
            Booking.objects.create(order_id=4, courier=courier, delivery_date=day)
    booking.cancel()
    reserve_courier(4, courier.pk, day + timedelta(days=1))
    assert courier in find_available_couriers(day, 60)
    assert Booking.objects.get(pk=booking.pk).status == Booking.Status.CANCELLED


def test_orm_create_update_delete(rollback_orm):
    client = Client.objects.create(name="Временный клиент", phone="+7")
    order = Order.objects.create(
        client=client, destination="Первый адрес", weight=1,
        status=Order.STATUS_CREATED,
    )
    order.destination = "Новый адрес"
    order.save(update_fields=["destination"])
    assert client.orders.get(pk=order.pk).destination == "Новый адрес"
    order.delete()
    assert not Order.objects.filter(pk=order.pk).exists()
    client.delete()
    assert not Client.objects.filter(pk=client.pk).exists()
