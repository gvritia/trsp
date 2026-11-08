"""Заказы, связанные с клиентами и курьерами через Django ORM."""

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Order(models.Model):
    STATUS_CREATED = "создан"
    STATUS_ASSIGNED = "назначен"
    STATUS_CANCELLED = "отменён"
    STATUS_DELIVERED = "доставлен"
    STATUSES = [
        (STATUS_CREATED, STATUS_CREATED),
        (STATUS_ASSIGNED, STATUS_ASSIGNED),
        (STATUS_CANCELLED, STATUS_CANCELLED),
        (STATUS_DELIVERED, STATUS_DELIVERED),
    ]

    destination = models.CharField(max_length=255)
    weight = models.FloatField(validators=[MinValueValidator(0.01)])
    client = models.ForeignKey(
        "homepage.Client", on_delete=models.PROTECT, related_name="orders"
    )
    courier = models.ForeignKey(
        "homepage.Courier",
        on_delete=models.PROTECT,
        related_name="orders",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20, choices=STATUSES, default=STATUS_CREATED
    )

    def __str__(self):
        return f"Заказ #{self.pk}: {self.destination}"

    def clean(self):
        if self.status == self.STATUS_ASSIGNED and self.courier_id is None:
            raise ValidationError("Назначенный заказ должен иметь курьера.")
        if self.pk and type(self).objects.filter(
            pk=self.pk, route_link__isnull=False
        ).exclude(courier_id=self.courier_id).exists():
            raise ValidationError(
                "Перед сменой курьера удалите заказ из маршрута."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
