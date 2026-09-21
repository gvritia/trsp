"""Функции планирования и завершения маршрутов доставки."""

from typing import Any

from couriers import Courier, get_courier
from orders import Order, get_order

Route = dict[str, Any]


def _next_route_id(routes: list[Route]) -> int:
    """Вернуть следующий свободный идентификатор маршрута."""
    return max((int(route["id"]) for route in routes), default=0) + 1


def get_route(routes: list[Route], route_id: int) -> Route:
    """Найти маршрут по идентификатору или вызвать исключение."""
    for route in routes:
        if route.get("id") == route_id:
            return route
    raise ValueError(f"маршрут #{route_id} не найден")


def create_route(
    routes: list[Route],
    orders: list[Order],
    couriers: list[Courier],
    courier_name: str,
    order_ids: list[int],
) -> Route:
    """Создать маршрут из назначенных выбранному курьеру заказов."""
    courier = get_courier(couriers, courier_name)
    canonical_name = str(courier["name"])
    unique_order_ids = list(dict.fromkeys(order_ids))
    if not unique_order_ids:
        raise ValueError("маршрут должен содержать хотя бы один заказ")

    active_route_orders = {
        order_id
        for route in routes
        if route.get("status") == "запланирован"
        for order_id in route.get("order_ids", [])
    }
    for order_id in unique_order_ids:
        order = get_order(orders, order_id)
        if order.get("status") != "назначен":
            raise ValueError(f"заказ #{order_id} не назначен курьеру")
        if order.get("courier") != canonical_name:
            raise ValueError(f"заказ #{order_id} назначен другому курьеру")
        if order_id in active_route_orders:
            raise ValueError(f"заказ #{order_id} уже включён в маршрут")

    route: Route = {
        "id": _next_route_id(routes),
        "courier": canonical_name,
        "order_ids": unique_order_ids,
        "status": "запланирован",
    }
    routes.append(route)
    return route


def complete_route(
    routes: list[Route], orders: list[Order], route_id: int
) -> bool:
    """Завершить маршрут и отметить связанные заказы доставленными."""
    route = get_route(routes, route_id)
    if route.get("status") == "завершён":
        raise ValueError(f"маршрут #{route_id} уже завершён")

    for order_id in route.get("order_ids", []):
        order = get_order(orders, int(order_id))
        order["status"] = "доставлен"
    route["status"] = "завершён"
    return True
