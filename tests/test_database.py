"""ПР7, 7.2 №10, №13, №29: связи, импорт и проверка запросов."""

import sqlite3
from pathlib import Path

import pytest

from db.bookings import (
    BookingError,
    cancel_booking,
    find_available_couriers,
    reserve_courier,
)
from db.database import connection, fetch_all, queries
from db.import_json import import_data
from db.migrate_routes import migrate_database


def test_import_is_repeatable_and_preserves_relations(tmp_path: Path) -> None:
    """Повторный импорт не дублирует данные и сохраняет внешние ключи."""
    source = Path(__file__).resolve().parent.parent / "data"
    database = tmp_path / "delivery.sqlite"
    for _ in range(2):
        import_data(source, database)
    with connection(database) as db:
        counts = {
            table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "clients",
                "couriers",
                "orders",
                "routes",
                "route_orders",
                "courier_bookings",
            )
        }
        assert counts == {
            "clients": 3,
            "couriers": 3,
            "orders": 4,
            "routes": 2,
            "route_orders": 2,
            "courier_bookings": 0,
        }
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        # ПР7, 7.6 №2: PRAGMA foreign_keys = ON включает проверку REFERENCES.
        # Клиента 999 нет, поэтому вставка заказа заканчивается IntegrityError.
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO orders "
                "(id, destination, weight, client_id, status) "
                "VALUES (99, 'Тест', 1, 999, 'создан')"
            )
        # То же правило действует для ссылки на курьера: 999 отсутствует.
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO orders "
                "(id, destination, weight, client_id, courier_id, status) "
                "VALUES (100, 'Тест', 1, 1, 999, 'назначен')"
            )


def test_all_named_queries_execute(tmp_path: Path) -> None:
    """Все примеры SQL исполняются на импортированной базе."""
    database = tmp_path / "delivery.sqlite"
    import_data(db_path=database)
    parameters = {
        "order_detail": (1,),
        "route_detail": (1,),
        "route_orders": (1,),
        "orders_search": ("%Мира%",) * 3,
        "orders_search_status": ("создан",) + ("%Мира%",) * 3,
        "orders_by_status_filter": ("создан",),
        "orders_page": (2, 0),
        "available_couriers": (60, "2026-10-20"),
        "booking_for_order": (3,),
    }
    assert len(queries()) >= 10
    with connection(database) as db:
        for name, query in queries().items():
            db.execute(query, parameters.get(name, ())).fetchall()
    busy_names = {
        row["name"] for row in fetch_all("busy_couriers", path=database)
    }
    assert busy_names == {
        "Иван",
        "Мария",
    }


def test_booking_availability_conflicts_cancellation_and_import(
    tmp_path: Path,
) -> None:
    """Бронь учитывает дату и вес, переживает импорт и отмену."""
    database = tmp_path / "delivery.sqlite"
    import_data(db_path=database)
    day = "2026-10-20"
    next_day = "2026-10-21"

    available = find_available_couriers(day, 60, database)
    assert [row["name"] for row in available] == [
        "Алексей"
    ]
    with pytest.raises(BookingError, match="грузоподъёмности"):
        reserve_courier(3, 1, day, database)
    booking_id = reserve_courier(3, 3, day, database)
    assert find_available_couriers(day, 60, database) == []
    available = find_available_couriers(next_day, 60, database)
    assert [row["name"] for row in available] == [
        "Алексей"
    ]
    with pytest.raises(BookingError, match="занят"):
        reserve_courier(4, 3, day, database)
    with pytest.raises(BookingError, match="уже имеет"):
        reserve_courier(3, 3, next_day, database)
    with pytest.raises(BookingError, match="дату"):
        find_available_couriers("2026-02-30", path=database)

    import_data(db_path=database)
    with connection(database) as db:
        count = db.execute(
            "SELECT COUNT(*) FROM courier_bookings"
        ).fetchone()[0]
        assert count == 1
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
    cancel_booking(booking_id, database)
    available = find_available_couriers(day, 60, database)
    assert [row["name"] for row in available] == [
        "Алексей"
    ]
    reserve_courier(4, 3, day, database)


def test_order_pagination_and_active_list(tmp_path: Path) -> None:
    """LIMIT/OFFSET возвращают разные страницы, IN исключает завершённые."""
    database = tmp_path / "delivery.sqlite"
    import_data(db_path=database)
    first = [row["id"] for row in fetch_all("orders_page", (2, 0), database)]
    second = [row["id"] for row in fetch_all("orders_page", (2, 2), database)]
    assert first == [1, 2]
    assert second == [3, 4]
    active_ids = [
        row["id"] for row in fetch_all("active_orders", path=database)
    ]
    assert active_ids == [
        1, 2, 3, 4
    ]


def test_route_courier_is_derived_and_database_rejects_mixed_routes(
    tmp_path: Path,
) -> None:
    """Курьер берётся из заказа; SQLite защищает состав маршрута."""
    database = tmp_path / "delivery.sqlite"
    import_data(db_path=database)
    with connection(database) as db:
        columns = {
            row["name"] for row in db.execute("PRAGMA table_info(routes)")
        }
        assert "courier_id" not in columns
        routes = db.execute(queries()["routes_list"]).fetchall()
        assert [row["courier_name"] for row in routes] == [
            "Иван", "Мария"
        ]
        db.execute(
            "INSERT INTO orders "
            "(id, destination, weight, client_id, courier_id, status) "
            "VALUES (99, 'Тест', 1, 1, 2, 'назначен')"
        )
        db.execute(
            "INSERT INTO orders "
            "(id, destination, weight, client_id, courier_id, status) "
            "VALUES (100, 'Тест', 1, 1, 1, 'назначен')"
        )
        db.execute(
            "INSERT INTO route_orders (route_id, order_id) VALUES (1, 100)"
        )
        with pytest.raises(sqlite3.IntegrityError, match="same courier"):
            db.execute(
                "INSERT INTO route_orders (route_id, order_id) "
                "VALUES (1, 99)"
            )
        with pytest.raises(sqlite3.IntegrityError, match="same courier"):
            db.execute(
                "UPDATE route_orders SET order_id = 99 "
                "WHERE route_id = 1 AND order_id = 1"
            )
        with pytest.raises(sqlite3.IntegrityError, match="changing courier"):
            db.execute("UPDATE orders SET courier_id = 2 WHERE id = 1")
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO route_orders (route_id, order_id) "
                "VALUES (1, 2)"
            )


def test_legacy_sqlite_route_migration_keeps_routes_and_links(
    tmp_path: Path,
) -> None:
    """Старая routes.courier_id удаляется без потери связанных строк."""
    database = tmp_path / "old.sqlite"
    with connection(database) as db:
        db.executescript(
            "CREATE TABLE clients ("
            "id INTEGER PRIMARY KEY, name TEXT, phone TEXT);"
            "CREATE TABLE couriers ("
            "id INTEGER PRIMARY KEY, name TEXT, "
            "capacity REAL, active INTEGER);"
            "CREATE TABLE orders ("
            "id INTEGER PRIMARY KEY, destination TEXT, weight REAL, "
            "client_id INTEGER REFERENCES clients(id), "
            "courier_id INTEGER REFERENCES couriers(id));"
            "CREATE TABLE routes ("
            "id INTEGER PRIMARY KEY, "
            "courier_id INTEGER NOT NULL REFERENCES couriers(id), "
            "status TEXT NOT NULL);"
            "CREATE TABLE route_orders ("
            "route_id INTEGER REFERENCES routes(id), "
            "order_id INTEGER REFERENCES orders(id), "
            "PRIMARY KEY (route_id, order_id));"
        )
        with db:
            db.execute("INSERT INTO clients VALUES (1, 'Анна', '+7')")
            db.execute("INSERT INTO couriers VALUES (1, 'Иван', 50, 1)")
            db.execute("INSERT INTO orders VALUES (7, 'Адрес', 1, 1, 1)")
            db.execute("INSERT INTO routes VALUES (5, 1, 'запланирован')")
            db.execute("INSERT INTO route_orders VALUES (5, 7)")

    assert migrate_database(database) is True
    assert migrate_database(database) is False
    with connection(database) as db:
        columns = {
            row["name"] for row in db.execute("PRAGMA table_info(routes)")
        }
        assert columns == {"id", "status"}
        assert tuple(db.execute("SELECT * FROM routes").fetchone()) == (
            5, "запланирован"
        )
        assert tuple(db.execute("SELECT * FROM route_orders").fetchone()) == (
            5, 7
        )
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
        triggers = {
            row["name"] for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type = 'trigger'"
            )
        }
        assert "route_order_same_courier_insert" in triggers
