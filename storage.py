"""Загрузка и сохранение данных проекта в формате JSON."""

import json
from pathlib import Path
from typing import Any

JsonRecord = dict[str, Any]


def load_records(file_path: Path) -> list[JsonRecord]:
    """Загрузить записи; для отсутствующего файла вернуть пустой список."""
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
    """Сохранить список словарей, автоматически создав каталог данных."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with file_path.open("w", encoding="utf-8") as destination:
            json.dump(records, destination, ensure_ascii=False, indent=2)
            destination.write("\n")
    except OSError as error:
        raise OSError(f"не удалось сохранить данные в {file_path}") from error


def load_orders(file_path: Path) -> list[JsonRecord]:
    """Загрузить заказы из JSON-файла."""
    return load_records(file_path)


def save_orders(file_path: Path, orders: list[JsonRecord]) -> None:
    """Сохранить заказы в JSON-файл."""
    save_records(file_path, orders)


def load_couriers(file_path: Path) -> list[JsonRecord]:
    """Загрузить курьеров из JSON-файла."""
    return load_records(file_path)


def save_couriers(file_path: Path, couriers: list[JsonRecord]) -> None:
    """Сохранить курьеров в JSON-файл."""
    save_records(file_path, couriers)


def load_clients(file_path: Path) -> list[JsonRecord]:
    """Загрузить клиентов из JSON-файла."""
    return load_records(file_path)


def save_clients(file_path: Path, clients: list[JsonRecord]) -> None:
    """Сохранить клиентов в JSON-файл."""
    save_records(file_path, clients)


def load_routes(file_path: Path) -> list[JsonRecord]:
    """Загрузить маршруты из JSON-файла."""
    return load_records(file_path)


def save_routes(file_path: Path, routes: list[JsonRecord]) -> None:
    """Сохранить маршруты в JSON-файл."""
    save_records(file_path, routes)
