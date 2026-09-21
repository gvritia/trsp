"""Функции работы с курьерами и распределения нагрузки."""

from typing import Any

from orders import Order, get_order

Courier = dict[str, Any]


def get_courier(couriers: list[Courier], courier_name: str) -> Courier:
    """Найти курьера без учёта регистра или вызвать исключение."""
    normalized_name = courier_name.strip().casefold()
    for courier in couriers:
        if str(courier.get("name", "")).casefold() == normalized_name:
            return courier
    raise ValueError(f"курьер {courier_name!r} не найден")


def courier_load(orders: list[Order], courier_name: str) -> float:
    """Рассчитать общий вес активных заказов курьера."""
    return sum(
        float(order["weight"])
        for order in orders
        if order.get("courier") == courier_name
        and order.get("status") == "назначен"
    )


def is_courier_available(
    couriers: list[Courier],
    orders: list[Order],
    courier_name: str,
    additional_weight: float = 0,
) -> bool:
    """Проверить активность курьера и запас его грузоподъёмности."""
    if additional_weight < 0:
        raise ValueError("вес заказа не может быть отрицательным")

    courier = get_courier(couriers, courier_name)
    if not courier.get("active", True):
        return False

    current_load = courier_load(orders, str(courier["name"]))
    return current_load + additional_weight <= float(courier["capacity"])


def assign_courier(
    orders: list[Order],
    couriers: list[Courier],
    order_id: int,
    courier_name: str,
) -> bool:
    """Назначить доступного курьера на созданный заказ."""
    order = get_order(orders, order_id)
    if order.get("status") != "создан":
        raise ValueError("назначить курьера можно только на созданный заказ")

    courier = get_courier(couriers, courier_name)
    canonical_name = str(courier["name"])
    if not is_courier_available(
        couriers, orders, canonical_name, float(order["weight"])
    ):
        raise ValueError(
            "курьер недоступен или его грузоподъёмность превышена"
        )

    order["courier"] = canonical_name
    order["status"] = "назначен"
    return True
