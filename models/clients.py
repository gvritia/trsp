"""Класс клиента и функции обработки коллекции клиентов."""

from typing import Any

from .people import Person


class Client(Person):
    """Заказчик доставки с проверяемым номером телефона."""

    def __init__(self, client_id: int, name: str, phone: str) -> None:
        super().__init__(client_id, name)
        self.phone = phone

    @property
    def role(self) -> str:
        """Вернуть название роли клиента."""
        return "Клиент"

    @property
    def phone(self) -> str:
        """Вернуть номер телефона клиента."""
        return self._phone

    @phone.setter
    def phone(self, value: str) -> None:
        """Проверить и сохранить номер телефона клиента."""
        value = value.strip()
        if not value:
            raise ValueError("телефон клиента не может быть пустым")
        self._phone = value

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> "Client":
        """Создать клиента из данных JSON."""
        return cls(int(data["id"]), str(data["name"]), str(data["phone"]))

    def to_data(self) -> dict[str, Any]:
        """Преобразовать клиента в данные для JSON."""
        return {"id": self.id, "name": self.name, "phone": self.phone}

    def __str__(self) -> str:
        """Вернуть строковое представление клиента."""
        return f"{super().__str__()} | {self.phone}"


def _next_client_id(clients: list[Client]) -> int:
    """Вернуть следующий свободный идентификатор клиента."""
    return max((client.id for client in clients), default=0) + 1


def add_client(clients: list[Client], name: str, phone: str) -> Client:
    """Создать объект клиента и добавить его в коллекцию."""
    normalized_phone = phone.strip()
    if any(client.phone == normalized_phone for client in clients):
        raise ValueError("клиент с таким телефоном уже существует")
    client = Client(_next_client_id(clients), name, normalized_phone)
    clients.append(client)
    return client


def get_client(clients: list[Client], client_id: int) -> Client:
    """Найти клиента по идентификатору или вызвать исключение."""
    for client in clients:
        if client.id == client_id:
            return client
    raise ValueError(f"клиент #{client_id} не найден")


def find_clients(clients: list[Client], query: str) -> list[Client]:
    """Найти клиентов по части имени или номера телефона."""
    normalized_query = query.strip().casefold()
    if not normalized_query:
        return []
    return [
        client
        for client in clients
        if normalized_query in client.name.casefold()
        or normalized_query in client.phone.casefold()
    ]
