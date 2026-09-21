"""Тесты взаимодействия объектов курьеров и заказов."""

import pytest

from models import Client, Courier, Order, Person
from models.orders import assign_courier


def courier_data() -> list[Courier]:
    """Вернуть тестовую коллекцию объектов Courier."""
    return [Courier(1, "Иван", 20.0)]


def test_courier_inherits_person_and_encapsulates_capacity() -> None:
    courier = courier_data()[0]

    assert isinstance(courier, Person)
    assert courier.capacity == 20.0
    assert "Курьер #1" in str(courier)

    with pytest.raises(ValueError, match="грузоподъёмность"):
        courier.capacity = 0


def test_assign_courier_links_objects() -> None:
    client = Client(1, "Анна", "+7-900-111-22-33")
    orders = [Order(1, "ул. Новая, 1", 12.0, client)]
    couriers = courier_data()

    assert assign_courier(orders, couriers, 1, "иван")
    assert orders[0].courier is couriers[0]
    assert orders[0].status == "назначен"


def test_courier_availability_accounts_for_object_load() -> None:
    client = Client(1, "Анна", "+7-900-111-22-33")
    courier = courier_data()[0]
    orders = [Order(1, "ул. Новая, 1", 12.0, client, "назначен", courier)]

    assert courier.is_available(orders, 8.0)
    assert not courier.is_available(orders, 8.1)
