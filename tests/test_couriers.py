"""Тесты распределения заказов между курьерами."""

import pytest

from couriers import assign_courier, is_courier_available


def courier_data() -> list[dict]:
    """Вернуть тестовый список курьеров."""
    return [{"id": 1, "name": "Иван", "capacity": 20.0, "active": True}]


def test_assign_courier_changes_order_status() -> None:
    orders = [
        {
            "id": 1,
            "destination": "ул. Новая, 1",
            "weight": 12.0,
            "status": "создан",
            "courier": None,
        }
    ]

    assert assign_courier(orders, courier_data(), 1, "иван")
    assert orders[0]["courier"] == "Иван"
    assert orders[0]["status"] == "назначен"


def test_courier_availability_accounts_for_current_load() -> None:
    orders = [
        {
            "id": 1,
            "destination": "ул. Новая, 1",
            "weight": 12.0,
            "status": "назначен",
            "courier": "Иван",
        }
    ]

    assert is_courier_available(courier_data(), orders, "Иван", 8.0)
    assert not is_courier_available(courier_data(), orders, "Иван", 8.1)


def test_assignment_rejects_overload() -> None:
    orders = [
        {
            "id": 1,
            "destination": "ул. Новая, 1",
            "weight": 21.0,
            "status": "создан",
            "courier": None,
        }
    ]

    with pytest.raises(ValueError, match="грузоподъёмность"):
        assign_courier(orders, courier_data(), 1, "Иван")
