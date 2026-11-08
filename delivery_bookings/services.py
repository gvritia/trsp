"""Правила бронирования поверх Django ORM."""

from datetime import date

from django.db import IntegrityError, transaction

from delivery_orders.models import Order
from homepage.models import Courier
from .models import Booking


class BookingError(ValueError):
    pass


def valid_delivery_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise BookingError("Укажите корректную дату доставки.") from exc


def find_available_couriers(day: date, weight: float = 0):
    occupied_ids = Booking.objects.active().for_date(day).values("courier_id")
    return (
        Courier.objects.filter(active=True, capacity__gte=weight)
        .exclude(pk__in=occupied_ids)
        .order_by("id")
    )


def reserve_courier(order_id: int, courier_id: int, day: date) -> Booking:
    with transaction.atomic():
        order = Order.objects.filter(pk=order_id).first()
        courier = Courier.objects.filter(pk=courier_id).first()
        if order is None or order.status != Order.STATUS_CREATED:
            raise BookingError("Выберите созданный заказ.")
        if Booking.objects.active().filter(order=order).exists():
            raise BookingError("Заказ уже имеет действующее бронирование.")
        if (
            courier is None
            or not courier.active
            or courier.capacity < order.weight
        ):
            raise BookingError(
                "Курьер неактивен или не подходит по грузоподъёмности."
            )
        if (
            Booking.objects.active()
            .for_date(day)
            .filter(courier=courier)
            .exists()
        ):
            raise BookingError("Курьер уже занят на эту дату.")
        try:
            # Уникальные ограничения защищают от двух одновременных запросов.
            with transaction.atomic():
                return Booking.objects.create(
                    order=order, courier=courier, delivery_date=day
                )
        except IntegrityError as exc:
            raise BookingError("Заказ или курьер уже забронирован.") from exc
