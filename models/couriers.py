"""Класс курьера и функции работы с курьерами."""

from typing import TYPE_CHECKING, Any

from .people import Person

if TYPE_CHECKING:
    from .orders import Order


class Courier(Person):
    """Исполнитель доставки с ограниченной грузоподъёмностью."""

    def __init__(
        self,
        courier_id: int,
        name: str,
        capacity: float,
        active: bool = True,
    ) -> None:
        super().__init__(courier_id, name)
        self.capacity = capacity
        self.active = active

    @property
    def role(self) -> str:
        """Вернуть название роли курьера."""
        return "Курьер"

    @property
    def capacity(self) -> float:
        """Вернуть грузоподъёмность курьера."""
        return self._capacity

    @capacity.setter
    def capacity(self, value: float) -> None:
        """Проверить и сохранить грузоподъёмность курьера."""
        if value <= 0:
            raise ValueError("грузоподъёмность должна быть больше нуля")
        self._capacity = float(value)

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> "Courier":
        """Создать курьера из данных JSON."""
        return cls(
            int(data["id"]),
            str(data["name"]),
            float(data["capacity"]),
            bool(data.get("active", True)),
        )

    def to_data(self) -> dict[str, Any]:
        """Преобразовать курьера в данные для JSON."""
        return {
            "id": self.id,
            "name": self.name,
            "capacity": self.capacity,
            "active": self.active,
        }

    def current_load(self, orders: list["Order"]) -> float:
        """Рассчитать общий вес назначенных курьеру заказов."""
        return sum(
            order.weight
            for order in orders
            if order.courier is self and order.status == "назначен"
        )

    def is_available(
        self, orders: list["Order"], additional_weight: float = 0
    ) -> bool:
        """Проверить активность и запас грузоподъёмности курьера."""
        if additional_weight < 0:
            raise ValueError("вес заказа не может быть отрицательным")
        return (
            self.active
            and self.current_load(orders) + additional_weight <= self.capacity
        )

    def __str__(self) -> str:
        """Вернуть строковое представление курьера."""
        state = "доступен" if self.active else "недоступен"
        return f"{super().__str__()} | {self.capacity:g} кг | {state}"


def get_courier(couriers: list[Courier], courier_id: int) -> Courier:
    """Найти курьера по идентификатору или вызвать исключение."""
    for courier in couriers:
        if courier.id == courier_id:
            return courier
    raise ValueError(f"курьер #{courier_id} не найден")


def find_courier(couriers: list[Courier], courier_name: str) -> Courier:
    """Найти курьера по имени без учёта регистра."""
    normalized_name = courier_name.strip().casefold()
    for courier in couriers:
        if courier.name.casefold() == normalized_name:
            return courier
    raise ValueError(f"курьер {courier_name!r} не найден")


def courier_load(orders: list["Order"], courier: Courier) -> float:
    """Вернуть текущую загрузку курьера через метод объекта."""
    return courier.current_load(orders)


def is_courier_available(
    couriers: list[Courier],
    orders: list["Order"],
    courier_name: str,
    additional_weight: float = 0,
) -> bool:
    """Найти курьера и проверить его доступность."""
    courier = find_courier(couriers, courier_name)
    return courier.is_available(orders, additional_weight)
