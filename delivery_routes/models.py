"""Маршруты и их связь с заказами."""

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


class Route(models.Model):
    status = models.CharField(
        "статус",
        max_length=20,
        choices=[("запланирован", "запланирован"), ("завершён", "завершён")],
        default="запланирован",
    )
    orders = models.ManyToManyField(
        "delivery_orders.Order", through="RouteOrder", related_name="routes"
    )
    slug = models.SlugField(
        "адрес страницы", unique=True, null=True, blank=True, editable=False
    )

    class Meta:
        verbose_name = "маршрут"
        verbose_name_plural = "маршруты"

    def __str__(self):
        return f"Маршрут #{self.pk}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.slug:
            self.slug = f"marshrut-{self.pk}"
            type(self).objects.filter(pk=self.pk).update(slug=self.slug)

    def get_absolute_url(self):
        return reverse("delivery_routes:slug_detail", args=[self.slug])


class RouteOrder(models.Model):
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name="links",
        verbose_name="маршрут",
    )
    order = models.OneToOneField(
        "delivery_orders.Order",
        on_delete=models.PROTECT,
        related_name="route_link",
        verbose_name="заказ",
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
        verbose_name = "заказ маршрута"
        verbose_name_plural = "заказы маршрута"
        constraints = [
            models.UniqueConstraint(
                fields=["route", "order"], name="unique_route_order"
            )
        ]
