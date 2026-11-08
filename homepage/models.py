"""Клиенты и курьеры системы доставки."""

from django.core.validators import MinValueValidator
from django.db import models


class Client(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=40)

    def __str__(self):
        return self.name


class Courier(models.Model):
    name = models.CharField(max_length=200)
    capacity = models.FloatField(validators=[MinValueValidator(0.01)])
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
