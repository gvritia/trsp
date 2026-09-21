"""Класс заказа и функции обработки коллекции заказов."""

from typing import Any, Iterator

from .clients import Client, get_client
from .couriers import Courier, find_courier, get_courier


class Order:
    """Заказ, связывающий клиента с назначенным курьером."""

    VALID_STATUSES = {"создан", "назначен", "отменён", "доставлен"}

    def __init__(
        self,
        order_id: int,
        destination: str,
        weight: float,
        client: Client,
        status: str = "создан",
        courier: Courier | None = None,
    ) -> None:
        if order_id < 1:
            raise ValueError("идентификатор заказа должен быть положительным")
        destination = destination.strip()
        if not destination:
            raise ValueError("адрес доставки не может быть пустым")
        if not self.validate_weight(weight):
            raise ValueError("вес должен быть больше нуля")
        if status not in self.VALID_STATUSES:
            raise ValueError(f"неизвестный статус заказа: {status}")
        if status == "назначен" and courier is None:
            raise ValueError("назначенный заказ должен содержать курьера")

        self.id = order_id
        self.destination = destination
        self.weight = float(weight)
        self.client = client
        self.status = status
        self.courier = courier

    @staticmethod
    def validate_weight(weight: float) -> bool:
        """Проверить корректность веса заказа."""
        return weight > 0

    @classmethod
    def from_data(
        cls,
        data: dict[str, Any],
        clients: list[Client],
        couriers: list[Courier],
    ) -> "Order":
        """Создать заказ из JSON и восстановить связи с объектами."""
        client = get_client(clients, int(data["client_id"]))
        courier: Courier | None = None
        courier_id = data.get("courier_id")
        if courier_id is not None:
            courier = get_courier(couriers, int(courier_id))
        elif data.get("courier"):
            courier = find_courier(couriers, str(data["courier"]))
        return cls(
            order_id=int(data["id"]),
            destination=str(data["destination"]),
            weight=float(data["weight"]),
            client=client,
            status=str(data.get("status", "создан")),
            courier=courier,
        )

    def to_data(self) -> dict[str, Any]:
        """Преобразовать заказ в данные для JSON."""
        return {
            "id": self.id,
            "destination": self.destination,
            "weight": self.weight,
            "client_id": self.client.id,
            "status": self.status,
            "courier_id": self.courier.id if self.courier else None,
        }

    def assign_courier(self, courier: Courier, orders: list["Order"]) -> None:
        """Назначить доступного курьера на созданный заказ."""
        if self.status != "создан":
            raise ValueError(
                "назначить курьера можно только на созданный заказ"
            )
        if not courier.is_available(orders, self.weight):
            raise ValueError(
                "курьер недоступен или его грузоподъёмность превышена"
            )
        self.courier = courier
        self.status = "назначен"

    def cancel(self) -> None:
        """Отменить заказ и освободить назначенного курьера."""
        if self.status == "отменён":
            raise ValueError(f"заказ #{self.id} уже отменён")
        if self.status == "доставлен":
            raise ValueError("доставленный заказ нельзя отменить")
        self.status = "отменён"
        self.courier = None

    def mark_delivered(self) -> None:
        """Отметить назначенный заказ доставленным."""
        if self.status != "назначен":
            raise ValueError("доставить можно только назначенный заказ")
        self.status = "доставлен"

    def __str__(self) -> str:
        """Вернуть строковое представление заказа."""
        courier_name = self.courier.name if self.courier else "не назначен"
        return (
            f"Заказ #{self.id}: {self.destination} | {self.weight:g} кг | "
            f"{self.status} | клиент: {self.client.name} | "
            f"курьер: {courier_name}"
        )


def _next_order_id(orders: list[Order]) -> int:
    """Вернуть следующий свободный идентификатор заказа."""
    return max((order.id for order in orders), default=0) + 1


def create_order(
    orders: list[Order],
    destination: str,
    weight: float,
    client: Client,
) -> Order:
    """Создать объект заказа и добавить его в коллекцию."""
    order = Order(_next_order_id(orders), destination, weight, client)
    orders.append(order)
    return order


def iter_active_orders(orders: list[Order]) -> Iterator[Order]:
    """Последовательно выдавать незавершённые и неотменённые заказы."""
    return (
        order
        for order in orders
        if order.status not in {"отменён", "доставлен"}
    )


def find_orders(orders: list[Order], query: str) -> list[Order]:
    """Найти заказы по адресу, клиенту или курьеру."""
    normalized_query = query.strip().casefold()
    if not normalized_query:
        return []
    return [
        order
        for order in orders
        if normalized_query in order.destination.casefold()
        or normalized_query in order.client.name.casefold()
        or (
            order.courier is not None
            and normalized_query in order.courier.name.casefold()
        )
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
        if order.weight <= maximum_weight
    ]


def sort_orders(
    orders: list[Order], key: str = "destination", reverse: bool = False
) -> list[Order]:
    """Вернуть новую коллекцию заказов, отсортированную по атрибуту."""
    key_functions = {
        "id": lambda order: order.id,
        "destination": lambda order: order.destination.casefold(),
        "weight": lambda order: order.weight,
        "status": lambda order: order.status,
        "client": lambda order: order.client.name.casefold(),
        "courier": lambda order: (
            order.courier.name.casefold() if order.courier else ""
        ),
    }
    if key not in key_functions:
        raise ValueError(f"сортировка по полю {key!r} не поддерживается")
    return sorted(orders, key=key_functions[key], reverse=reverse)


def get_order(orders: list[Order], order_id: int) -> Order:
    """Найти заказ по идентификатору или вызвать исключение."""
    for order in orders:
        if order.id == order_id:
            return order
    raise ValueError(f"заказ #{order_id} не найден")


def assign_courier(
    orders: list[Order],
    couriers: list[Courier],
    order_id: int,
    courier_name: str,
) -> bool:
    """Найти объекты заказа и курьера и организовать их взаимодействие."""
    order = get_order(orders, order_id)
    courier = find_courier(couriers, courier_name)
    order.assign_courier(courier, orders)
    return True


def cancel_order(orders: list[Order], order_id: int) -> bool:
    """Найти заказ и вызвать его метод отмены."""
    get_order(orders, order_id).cancel()
    return True


def calculate_efficiency(orders: list[Order]) -> float:
    """Рассчитать процент назначенных среди активных заказов."""
    active_orders = list(iter_active_orders(orders))
    if not active_orders:
        return 0.0
    assigned = sum(order.status == "назначен" for order in active_orders)
    return assigned / len(active_orders) * 100


def get_order_status(order: Order) -> str:
    """Вернуть текстовое описание текущего состояния заказа."""
    status_messages = {
        "создан": "Заказ ожидает назначения курьера",
        "назначен": "Курьер назначен",
        "отменён": "Заказ отменён",
        "доставлен": "Заказ доставлен",
    }
    return status_messages[order.status]
