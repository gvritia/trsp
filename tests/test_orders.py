"""Тесты функций обработки заказов."""

import pytest

from orders import (
    calculate_efficiency,
    cancel_order,
    create_order,
    filter_orders_by_weight,
    find_orders,
    sort_orders,
)


def test_create_order_adds_valid_order() -> None:
    orders = []

    order = create_order(orders, "ул. Новая, 1", 12.5)

    assert order["id"] == 1
    assert order["status"] == "создан"
    assert orders == [order]


def test_create_order_rejects_non_positive_weight() -> None:
    with pytest.raises(ValueError, match="вес"):
        create_order([], "ул. Новая, 1", 0)


def test_search_filter_and_sort_do_not_change_source() -> None:
    orders = [
        {
            "id": 1,
            "destination": "ул. Ленина, 15",
            "weight": 25.5,
            "status": "создан",
            "courier": None,
        },
        {
            "id": 2,
            "destination": "пр. Мира, 10",
            "weight": 10.0,
            "status": "назначен",
            "courier": "Мария",
        },
    ]

    assert find_orders(orders, "мира")[0]["id"] == 2
    assert filter_orders_by_weight(orders, 20)[0]["id"] == 2
    assert [order["id"] for order in sort_orders(orders, "weight")] == [2, 1]
    assert [order["id"] for order in orders] == [1, 2]


def test_cancel_order_excludes_it_from_efficiency() -> None:
    orders = [
        {
            "id": 1,
            "destination": "ул. Новая, 1",
            "weight": 5.0,
            "status": "назначен",
            "courier": "Иван",
        },
        {
            "id": 2,
            "destination": "ул. Садовая, 2",
            "weight": 10.0,
            "status": "создан",
            "courier": None,
        },
    ]

    cancel_order(orders, 2)

    assert orders[1]["status"] == "отменён"
    assert calculate_efficiency(orders) == 100.0
