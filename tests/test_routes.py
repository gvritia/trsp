"""Тесты функций планирования маршрутов."""

import pytest

from routes import complete_route, create_route


def sample_couriers() -> list[dict]:
    """Вернуть тестовый список курьеров."""
    return [{"id": 1, "name": "Иван", "capacity": 50.0, "active": True}]


def sample_orders() -> list[dict]:
    """Вернуть назначенный тестовый заказ."""
    return [
        {
            "id": 1,
            "destination": "ул. Новая, 1",
            "weight": 12.0,
            "client_id": 1,
            "status": "назначен",
            "courier": "Иван",
        }
    ]


def test_create_and_complete_route() -> None:
    routes = []
    orders = sample_orders()

    route = create_route(routes, orders, sample_couriers(), "иван", [1])
    complete_route(routes, orders, route["id"])

    assert route["status"] == "завершён"
    assert orders[0]["status"] == "доставлен"


def test_route_rejects_order_of_another_courier() -> None:
    orders = sample_orders()
    orders[0]["courier"] = "Мария"

    with pytest.raises(ValueError, match="другому курьеру"):
        create_route([], orders, sample_couriers(), "Иван", [1])
