"""ПР7, 7.6 №1: операции с бронями через sqlite3, без Django ORM.

Этот модуль использует подключение из db/database.py и таблицу
courier_bookings из sql/schema.sql. Брони создаются через сайт.
"""

import sqlite3
from datetime import date
from pathlib import Path

from db.database import connection, fetch_all, queries


class BookingError(ValueError):
    """Понятная пользователю ошибка резервирования."""


def valid_delivery_date(value: str) -> str:
    """Принять только настоящую календарную дату в формате ГГГГ-ММ-ДД."""
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError) as error:
        raise BookingError("Укажите дату в формате ГГГГ-ММ-ДД.") from error
    if parsed.isoformat() != value:
        raise BookingError("Укажите дату в формате ГГГГ-ММ-ДД.")
    return value


def find_available_couriers(
    delivery_date: str, weight: float = 0, path: Path | None = None
) -> list[sqlite3.Row]:
    """Найти свободных активных курьеров с нужной грузоподъёмностью."""
    valid_delivery_date(delivery_date)
    if weight < 0:
        raise BookingError("Вес заказа не может быть отрицательным.")
    # ПР7, 7.2 №25: дата и вес передаются параметрами, а не вставляются в SQL.
    return fetch_all("available_couriers", (weight, delivery_date), path)


def reserve_courier(
    order_id: int,
    courier_id: int,
    delivery_date: str,
    path: Path | None = None,
) -> int:
    """Атомарно забронировать курьера для созданного заказа."""
    valid_delivery_date(delivery_date)
    with connection(path) as db:
        try:
            # BEGIN IMMEDIATE и уникальные индексы из schema.sql не дают
            # двум запросам одновременно занять курьера на одну дату.
            db.execute("BEGIN IMMEDIATE")
            order = db.execute(
                "SELECT weight, status FROM orders WHERE id = ?", (order_id,)
            ).fetchone()
            if order is None or order["status"] != "создан":
                raise BookingError(
                    "Для бронирования нужен существующий созданный заказ."
                )
            if db.execute(
                "SELECT 1 FROM courier_bookings "
                "WHERE order_id = ? AND is_cancelled = 0", (order_id,)
            ).fetchone():
                raise BookingError(
                    "Этот заказ уже имеет действующее бронирование."
                )
            available = db.execute(
                queries()["available_couriers"],
                (order["weight"], delivery_date),
            ).fetchall()
            if courier_id not in {row["id"] for row in available}:
                raise BookingError(
                    "Курьер занят, неактивен или не подходит "
                    "по грузоподъёмности."
                )
            cursor = db.execute(
                "INSERT INTO courier_bookings "
                "(order_id, courier_id, delivery_date) VALUES (?, ?, ?)",
                (order_id, courier_id, delivery_date),
            )
            db.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError as error:
            db.rollback()
            raise BookingError("Курьер или заказ уже забронирован.") from error
        except Exception:
            db.rollback()
            raise


def cancel_booking(booking_id: int, path: Path | None = None) -> None:
    """Отменить действующую бронь, сохранив запись для истории."""
    with connection(path) as db:
        try:
            db.execute("BEGIN IMMEDIATE")
            updated = db.execute(
                "UPDATE courier_bookings SET is_cancelled = 1 "
                "WHERE id = ? AND is_cancelled = 0", (booking_id,)
            )
            if updated.rowcount != 1:
                raise BookingError("Действующее бронирование не найдено.")
            db.commit()
        except Exception:
            db.rollback()
            raise
