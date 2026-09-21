"""Объектная модель системы планирования доставки."""

from .clients import Client
from .couriers import Courier
from .orders import Order
from .people import Person
from .routes import Route

__all__ = ["Client", "Courier", "Order", "Person", "Route"]
