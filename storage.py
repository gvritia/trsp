"""Загрузка и сохранение объектной модели в формате JSON."""

import json
from pathlib import Path
from typing import Any

from models import Client, Courier, Order, Route

JsonRecord = dict[str, Any]


def load_records(file_path: Path) -> list[JsonRecord]:
    """Загрузить JSON-записи или вернуть пустой список."""
    try:
        with file_path.open("r", encoding="utf-8") as source:
            data = json.load(source)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as error:
        raise ValueError(f"повреждён JSON-файл {file_path}") from error

    if not isinstance(data, list) or not all(
        isinstance(item, dict) for item in data
    ):
        raise ValueError(f"ожидался список объектов в файле {file_path}")
    return data


def save_records(file_path: Path, records: list[JsonRecord]) -> None:
    """Сохранить JSON-записи, автоматически создав каталог данных."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with file_path.open("w", encoding="utf-8") as destination:
            json.dump(records, destination, ensure_ascii=False, indent=2)
            destination.write("\n")
    except OSError as error:
        raise OSError(f"не удалось сохранить данные в {file_path}") from error


def load_clients(file_path: Path) -> list[Client]:
    """Загрузить клиентов и создать объекты Client."""
    return [Client.from_data(data) for data in load_records(file_path)]


def save_clients(file_path: Path, clients: list[Client]) -> None:
    """Преобразовать клиентов в JSON-данные и сохранить."""
    save_records(file_path, [client.to_data() for client in clients])


def load_couriers(file_path: Path) -> list[Courier]:
    """Загрузить курьеров и создать объекты Courier."""
    return [Courier.from_data(data) for data in load_records(file_path)]


def save_couriers(file_path: Path, couriers: list[Courier]) -> None:
    """Преобразовать курьеров в JSON-данные и сохранить."""
    save_records(file_path, [courier.to_data() for courier in couriers])


def load_orders(
    file_path: Path,
    clients: list[Client],
    couriers: list[Courier],
) -> list[Order]:
    """Загрузить заказы и восстановить связи с клиентами и курьерами."""
    return [
        Order.from_data(data, clients, couriers)
        for data in load_records(file_path)
    ]


def save_orders(file_path: Path, orders: list[Order]) -> None:
    """Преобразовать заказы в JSON-данные и сохранить."""
    save_records(file_path, [order.to_data() for order in orders])


def load_routes(
    file_path: Path,
    orders: list[Order],
    couriers: list[Courier],
) -> list[Route]:
    """Загрузить маршруты и восстановить связи с заказами и курьерами."""
    return [
        Route.from_data(data, orders, couriers)
        for data in load_records(file_path)
    ]


def save_routes(file_path: Path, routes: list[Route]) -> None:
    """Преобразовать маршруты в JSON-данные и сохранить."""
    save_records(file_path, [route.to_data() for route in routes])
