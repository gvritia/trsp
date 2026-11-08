"""Тесты объектной модели маршрутов."""

import pytest

from models import Client, Courier, Order, Route
from models.orders import cancel_order
from models.routes import complete_route, create_route


def sample_graph() -> tuple[list[Courier], list[Order]]:
    """Вернуть связанные объекты курьера и назначенного заказа."""
    client = Client(1, "Анна", "+7-900-111-22-33")
    courier = Courier(1, "Иван", 50.0)
    order = Order(1, "ул. Новая, 1", 12.0, client, "назначен", courier)
    return [courier], [order]


def test_create_and_complete_route_changes_object_states() -> None:
    couriers, orders = sample_graph()
    routes: list[Route] = []

    route = create_route(routes, orders, couriers, "иван", [1])
    complete_route(routes, orders, route.id)

    assert route.courier is couriers[0]
    assert "courier" not in vars(route)
    assert route.orders[0] is orders[0]
    assert route.status == "завершён"
    assert orders[0].status == "доставлен"


def test_route_rejects_order_of_another_courier() -> None:
    couriers, orders = sample_graph()
    orders[0].courier = Courier(2, "Мария", 50.0)

    with pytest.raises(ValueError, match="другому курьеру"):
        create_route([], orders, couriers, "Иван", [1])


def test_route_rejects_orders_of_different_couriers() -> None:
    couriers, orders = sample_graph()
    orders.append(
        Order(2, "ул. Новая, 2", 5.0, orders[0].client,
              "назначен", Courier(2, "Мария", 50.0))
    )
    with pytest.raises(ValueError, match="одного курьера"):
        Route(1, orders)


def test_routed_order_cannot_lose_its_courier() -> None:
    couriers, orders = sample_graph()
    route = create_route([], orders, couriers, "Иван", [1])
    with pytest.raises(ValueError, match="включённый в маршрут"):
        cancel_order(orders, 1, [route])
    assert route.courier is couriers[0]
