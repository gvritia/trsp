"""Бронирования курьеров и методы выборки по статусу."""

from django.db import models
from django.db.models import Q


class BookingQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status=Booking.Status.ACTIVE)

    def cancelled(self):
        return self.filter(status=Booking.Status.CANCELLED)

    def completed(self):
        return self.filter(status=Booking.Status.COMPLETED)

    def for_date(self, day):
        return self.filter(delivery_date=day)


class Booking(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Действует"
        CANCELLED = "cancelled", "Отменено"
        COMPLETED = "completed", "Завершено"

    order = models.ForeignKey(
        "delivery_orders.Order",
        on_delete=models.PROTECT,
        related_name="bookings",
        verbose_name="заказ",
    )
    courier = models.ForeignKey(
        "homepage.Courier",
        on_delete=models.PROTECT,
        related_name="bookings",
        verbose_name="курьер",
    )
    delivery_date = models.DateField("дата доставки")
    status = models.CharField(
        "статус", max_length=10, choices=Status.choices, default=Status.ACTIVE
    )
    objects = BookingQuerySet.as_manager()

    class Meta:
        verbose_name = "бронирование"
        verbose_name_plural = "бронирования"
        constraints = [
            models.UniqueConstraint(
                fields=["courier", "delivery_date"],
                condition=Q(status="active"),
                name="unique_active_courier_date",
            ),
            models.UniqueConstraint(
                fields=["order"],
                condition=Q(status="active"),
                name="unique_active_order_booking",
            ),
        ]

    def __str__(self):
        return f"Бронирование #{self.pk} — заказ #{self.order_id}"

    def cancel(self):
        if self.status != self.Status.ACTIVE:
            raise ValueError("Действующее бронирование не найдено.")
        self.status = self.Status.CANCELLED
        self.save(update_fields=["status"])
