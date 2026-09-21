"""Функции работы с клиентами системы доставки."""

from typing import Any

Client = dict[str, Any]


def _next_client_id(clients: list[Client]) -> int:
    """Вернуть следующий свободный идентификатор клиента."""
    return max((int(client["id"]) for client in clients), default=0) + 1


def add_client(clients: list[Client], name: str, phone: str) -> Client:
    """Добавить клиента после проверки имени и уникальности телефона."""
    name = name.strip()
    phone = phone.strip()
    if not name:
        raise ValueError("имя клиента не может быть пустым")
    if not phone:
        raise ValueError("телефон клиента не может быть пустым")
    if any(client.get("phone") == phone for client in clients):
        raise ValueError("клиент с таким телефоном уже существует")

    client: Client = {
        "id": _next_client_id(clients),
        "name": name,
        "phone": phone,
    }
    clients.append(client)
    return client


def get_client(clients: list[Client], client_id: int) -> Client:
    """Найти клиента по идентификатору или вызвать исключение."""
    for client in clients:
        if client.get("id") == client_id:
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
        if normalized_query in str(client.get("name", "")).casefold()
        or normalized_query in str(client.get("phone", "")).casefold()
    ]
