"""Бронирования курьера на дату с сохранением отменённой истории."""

from django.db import models
from django.db.models import Q


class Booking(models.Model):
    order = models.ForeignKey(
        "delivery_orders.Order",
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    courier = models.ForeignKey(
        "homepage.Courier", on_delete=models.PROTECT, related_name="bookings"
    )
    delivery_date = models.DateField()
    is_cancelled = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["courier", "delivery_date"],
                condition=Q(is_cancelled=False),
                name="unique_active_courier_date",
            ),
            models.UniqueConstraint(
                fields=["order"],
                condition=Q(is_cancelled=False),
                name="unique_active_order_booking",
            ),
        ]

    def cancel(self):
        if self.is_cancelled:
            raise ValueError("Действующее бронирование не найдено.")
        self.is_cancelled = True
        self.save(update_fields=["is_cancelled"])
