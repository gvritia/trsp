"""Тесты объектной модели заказов."""

import pytest

from models import Client, Courier, Order
from models.orders import (
    calculate_efficiency,
    cancel_order,
    create_order,
    filter_orders_by_weight,
    find_orders,
    sort_orders,
)


def test_create_order_links_client_object() -> None:
    client = Client(1, "Анна", "+7-900-111-22-33")
    orders: list[Order] = []

    order = create_order(orders, "ул. Новая, 1", 12.5, client)

    assert order.id == 1
    assert order.client is client
    assert order.status == "создан"
    assert orders == [order]


def test_order_rejects_non_positive_weight() -> None:
    client = Client(1, "Анна", "+7-900-111-22-33")

    with pytest.raises(ValueError, match="вес"):
        Order(1, "ул. Новая, 1", 0, client)


def test_search_filter_and_sort_work_with_objects() -> None:
    client = Client(1, "Анна", "+7-900-111-22-33")
    courier = Courier(1, "Иван", 50.0)
    orders = [
        Order(1, "ул. Ленина, 15", 25.5, client),
        Order(2, "пр. Мира, 10", 10.0, client, "назначен", courier),
    ]

    assert find_orders(orders, "мира") == [orders[1]]
    assert filter_orders_by_weight(orders, 20) == [orders[1]]
    assert [order.id for order in sort_orders(orders, "weight")] == [2, 1]
    assert [order.id for order in orders] == [1, 2]


def test_cancel_method_excludes_order_from_efficiency() -> None:
    client = Client(1, "Анна", "+7-900-111-22-33")
    courier = Courier(1, "Иван", 50.0)
    orders = [
        Order(1, "ул. Новая, 1", 5.0, client, "назначен", courier),
        Order(2, "ул. Садовая, 2", 10.0, client),
    ]

    cancel_order(orders, 2)

    assert orders[1].status == "отменён"
    assert orders[1].courier is None
    assert calculate_efficiency(orders) == 100.0
