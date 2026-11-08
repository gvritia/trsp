"""Клиенты и курьеры системы доставки."""

from django.core.validators import MinValueValidator
from django.db import models


class Client(models.Model):
    name = models.CharField("имя", max_length=200)
    phone = models.CharField("телефон", max_length=40)

    class Meta:
        verbose_name = "клиент"
        verbose_name_plural = "клиенты"

    def __str__(self):
        return self.name


class Courier(models.Model):
    name = models.CharField("имя", max_length=200)
    capacity = models.FloatField(
        "грузоподъёмность", validators=[MinValueValidator(0.01)]
    )
    active = models.BooleanField("активен", default=True)

    class Meta:
        verbose_name = "курьер"
        verbose_name_plural = "курьеры"

    def __str__(self):
        return self.name
