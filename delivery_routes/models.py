"""Маршруты и их связь с заказами."""

from django.core.exceptions import ValidationError
from django.db import models


class Route(models.Model):
    status = models.CharField(
        max_length=20,
        choices=[("запланирован", "запланирован"), ("завершён", "завершён")],
        default="запланирован",
    )
    orders = models.ManyToManyField(
        "delivery_orders.Order", through="RouteOrder", related_name="routes"
    )

    def __str__(self):
        return f"Маршрут #{self.pk}"


class RouteOrder(models.Model):
    route = models.ForeignKey(
        Route, on_delete=models.CASCADE, related_name="links"
    )
    order = models.OneToOneField(
        "delivery_orders.Order",
        on_delete=models.PROTECT,
        related_name="route_link",
    )

    def clean(self):
        if not self.route_id or not self.order_id:
            return
        if self.order.courier_id is None:
            raise ValidationError("Заказ маршрута должен иметь курьера.")
        existing = RouteOrder.objects.filter(route_id=self.route_id).exclude(
            pk=self.pk
        )
        if existing.exclude(order__courier_id=self.order.courier_id).exists():
            raise ValidationError(
                "У заказов маршрута должен быть один курьер."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["route", "order"], name="unique_route_order"
            )
        ]
