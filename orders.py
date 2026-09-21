"""Функции создания, поиска и обработки заказов."""

from typing import Any, Iterator

Order = dict[str, Any]


def _next_order_id(orders: list[Order]) -> int:
    """Вернуть следующий свободный идентификатор заказа."""
    return max((int(order["id"]) for order in orders), default=0) + 1


def create_order(
    orders: list[Order],
    destination: str,
    weight: float,
    client_id: int | None = None,
) -> Order:
    """Создать новый заказ и добавить его в переданный список."""
    destination = destination.strip()
    if not destination:
        raise ValueError("адрес доставки не может быть пустым")
    if weight <= 0:
        raise ValueError("вес должен быть больше нуля")

    order: Order = {
        "id": _next_order_id(orders),
        "destination": destination,
        "weight": float(weight),
        "client_id": client_id,
        "status": "создан",
        "courier": None,
    }
    orders.append(order)
    return order


def iter_active_orders(orders: list[Order]) -> Iterator[Order]:
    """Последовательно выдавать все неотменённые заказы."""
    return (order for order in orders if order.get("status") != "отменён")


def find_orders(orders: list[Order], query: str) -> list[Order]:
    """Найти заказы по части адреса или имени курьера."""
    normalized_query = query.strip().casefold()
    if not normalized_query:
        return []

    return [
        order
        for order in orders
        if normalized_query in str(order.get("destination", "")).casefold()
        or normalized_query in str(order.get("courier") or "").casefold()
    ]


def filter_orders_by_weight(
    orders: list[Order], maximum_weight: float
) -> list[Order]:
    """Отобрать активные заказы не тяжелее указанного веса."""
    if maximum_weight < 0:
        raise ValueError("максимальный вес не может быть отрицательным")
    return [
        order
        for order in iter_active_orders(orders)
        if float(order["weight"]) <= maximum_weight
    ]


def sort_orders(
    orders: list[Order], key: str = "destination", reverse: bool = False
) -> list[Order]:
    """Вернуть новую коллекцию заказов, отсортированную по указанному полю."""
    allowed_keys = {
        "id",
        "destination",
        "weight",
        "client_id",
        "status",
        "courier",
    }
    if key not in allowed_keys:
        raise ValueError(f"сортировка по полю {key!r} не поддерживается")

    return sorted(
        orders,
        key=lambda order: (order.get(key) is None, order.get(key)),
        reverse=reverse,
    )


def get_order(orders: list[Order], order_id: int) -> Order:
    """Найти заказ по идентификатору или вызвать исключение."""
    for order in orders:
        if order.get("id") == order_id:
            return order
    raise ValueError(f"заказ #{order_id} не найден")


def cancel_order(orders: list[Order], order_id: int) -> bool:
    """Отменить созданный или назначенный заказ."""
    order = get_order(orders, order_id)
    if order.get("status") == "отменён":
        raise ValueError(f"заказ #{order_id} уже отменён")

    order["status"] = "отменён"
    order["courier"] = None
    return True


def calculate_efficiency(orders: list[Order]) -> float:
    """Рассчитать процент назначенных среди всех активных заказов."""
    active_orders = list(iter_active_orders(orders))
    if not active_orders:
        return 0.0

    assigned = sum(
        order.get("status") == "назначен" for order in active_orders
    )
    return assigned / len(active_orders) * 100


def get_order_status(order: Order) -> str:
    """Вернуть текстовое описание статуса заказа из сценария ПР1."""
    status_messages = {
        "создан": "Заказ ожидает назначения курьера",
        "назначен": "Курьер назначен",
        "отменён": "Заказ отменён",
    }
    return status_messages.get(str(order.get("status")), "Статус неизвестен")
