"""Класс маршрута и функции обработки коллекции маршрутов."""

from typing import Any

from .couriers import Courier, find_courier, get_courier
from .orders import Order, get_order


class Route:
    """Маршрут курьера, объединяющий несколько заказов."""

    VALID_STATUSES = {"запланирован", "завершён"}

    def __init__(
        self,
        route_id: int,
        courier: Courier,
        orders: list[Order],
        status: str = "запланирован",
    ) -> None:
        if route_id < 1:
            raise ValueError(
                "идентификатор маршрута должен быть положительным"
            )
        if not orders:
            raise ValueError("маршрут должен содержать хотя бы один заказ")
        if status not in self.VALID_STATUSES:
            raise ValueError(f"неизвестный статус маршрута: {status}")
        self.id = route_id
        self.courier = courier
        self.orders = orders
        self.status = status

    @classmethod
    def from_data(
        cls,
        data: dict[str, Any],
        orders: list[Order],
        couriers: list[Courier],
    ) -> "Route":
        """Создать маршрут из JSON и восстановить объектные связи."""
        courier_id = data.get("courier_id")
        if courier_id is not None:
            courier = get_courier(couriers, int(courier_id))
        else:
            courier = find_courier(couriers, str(data["courier"]))
        route_orders = [
            get_order(orders, int(order_id))
            for order_id in data.get("order_ids", [])
        ]
        return cls(
            int(data["id"]),
            courier,
            route_orders,
            str(data.get("status", "запланирован")),
        )

    def to_data(self) -> dict[str, Any]:
        """Преобразовать маршрут в данные для JSON."""
        return {
            "id": self.id,
            "courier_id": self.courier.id,
            "order_ids": [order.id for order in self.orders],
            "status": self.status,
        }

    def complete(self) -> None:
        """Завершить маршрут и доставить все связанные заказы."""
        if self.status == "завершён":
            raise ValueError(f"маршрут #{self.id} уже завершён")
        for order in self.orders:
            order.mark_delivered()
        self.status = "завершён"

    def __str__(self) -> str:
        """Вернуть строковое представление маршрута."""
        order_numbers = ", ".join(str(order.id) for order in self.orders)
        return (
            f"Маршрут #{self.id}: курьер {self.courier.name} | "
            f"заказы: {order_numbers} | {self.status}"
        )


def _next_route_id(routes: list[Route]) -> int:
    """Вернуть следующий свободный идентификатор маршрута."""
    return max((route.id for route in routes), default=0) + 1


def get_route(routes: list[Route], route_id: int) -> Route:
    """Найти маршрут по идентификатору или вызвать исключение."""
    for route in routes:
        if route.id == route_id:
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
    courier = find_courier(couriers, courier_name)
    unique_order_ids = list(dict.fromkeys(order_ids))
    if not unique_order_ids:
        raise ValueError("маршрут должен содержать хотя бы один заказ")

    active_route_orders = {
        order.id
        for route in routes
        if route.status == "запланирован"
        for order in route.orders
    }
    route_orders = []
    for order_id in unique_order_ids:
        order = get_order(orders, order_id)
        if order.status != "назначен":
            raise ValueError(f"заказ #{order_id} не назначен курьеру")
        if order.courier is not courier:
            raise ValueError(f"заказ #{order_id} назначен другому курьеру")
        if order_id in active_route_orders:
            raise ValueError(f"заказ #{order_id} уже включён в маршрут")
        route_orders.append(order)

    route = Route(_next_route_id(routes), courier, route_orders)
    routes.append(route)
    return route


def complete_route(
    routes: list[Route], orders: list[Order], route_id: int
) -> bool:
    """Найти маршрут и вызвать его метод завершения."""
    route = get_route(routes, route_id)
    route.complete()
    return True
