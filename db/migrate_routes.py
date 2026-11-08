"""Однократный перенос старой схемы маршрутов без потери записей SQLite."""

import sqlite3
from pathlib import Path

from db.database import BASE_DIR, connection


def migrate_routes_without_courier(db: sqlite3.Connection) -> bool:
    """Удалить дублирующий routes.courier_id, сохранив маршруты и связи."""
    columns = {
        row["name"] for row in db.execute("PRAGMA table_info(routes)")
    }
    if "courier_id" not in columns:
        return False

    # Для перестройки таблиц SQLite нужно выключить FK до начала транзакции.
    # Проверка данных и изменение схемы проходят под одной блокировкой записи.
    db.execute("PRAGMA foreign_keys = OFF")
    try:
        db.execute("BEGIN IMMEDIATE")
        old_violations = db.execute("PRAGMA foreign_key_check").fetchall()
        if old_violations:
            raise sqlite3.IntegrityError(
                f"Нарушены внешние ключи до миграции: {old_violations}"
            )
        problems = db.execute(
            "SELECT r.id FROM routes AS r "
            "LEFT JOIN route_orders AS ro ON ro.route_id = r.id "
            "LEFT JOIN orders AS o ON o.id = ro.order_id "
            "GROUP BY r.id, r.courier_id "
            "HAVING COUNT(ro.order_id) = 0 "
            "OR COUNT(DISTINCT o.courier_id) <> 1 "
            "OR MIN(o.courier_id) <> r.courier_id "
            "OR SUM(CASE WHEN ro.order_id IS NOT NULL "
            "AND o.courier_id IS NULL THEN 1 ELSE 0 END) > 0"
        ).fetchall()
        if problems:
            ids = ", ".join(str(row["id"]) for row in problems)
            raise ValueError(
                f"Маршруты {ids}: курьер не определяется по заказам. "
                "Исправьте данные перед миграцией."
            )
        duplicate = db.execute(
            "SELECT order_id FROM route_orders GROUP BY order_id "
            "HAVING COUNT(*) > 1 LIMIT 1"
        ).fetchone()
        if duplicate:
            raise ValueError(
                f"Заказ #{duplicate['order_id']} входит в несколько маршрутов."
            )

        route_rows = db.execute(
            "SELECT id, status FROM routes ORDER BY id"
        ).fetchall()
        link_rows = db.execute(
            "SELECT route_id, order_id FROM route_orders "
            "ORDER BY route_id, order_id"
        ).fetchall()

        # Сначала удаляем дочернюю таблицу, затем таблицу маршрутов.
        # Имена и ID сохраняются при вставке в новые таблицы.
        db.execute("DROP TABLE route_orders")
        db.execute("DROP TABLE routes")
        db.execute(
            "CREATE TABLE routes ("
            "id INTEGER PRIMARY KEY, "
            "status TEXT NOT NULL "
            "CHECK (status IN ('запланирован', 'завершён')))"
        )
        db.execute(
            "CREATE TABLE route_orders ("
            "route_id INTEGER NOT NULL "
            "REFERENCES routes(id) ON DELETE CASCADE, "
            "order_id INTEGER NOT NULL REFERENCES orders(id), "
            "PRIMARY KEY (route_id, order_id), UNIQUE (order_id))"
        )
        db.executemany(
            "INSERT INTO routes (id, status) VALUES (?, ?)",
            [tuple(row) for row in route_rows],
        )
        db.executemany(
            "INSERT INTO route_orders (route_id, order_id) VALUES (?, ?)",
            [tuple(row) for row in link_rows],
        )
        violations = db.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise sqlite3.IntegrityError(
                f"Нарушены внешние ключи после миграции: {violations}"
            )
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.execute("PRAGMA foreign_keys = ON")


def migrate_database(path: Path | None = None) -> bool:
    """Перестроить старую таблицу и установить актуальные ограничения."""
    with connection(path) as db:
        changed = migrate_routes_without_courier(db)
        schema = (BASE_DIR / "sql" / "schema.sql").read_text(encoding="utf-8")
        db.executescript(schema)
        return changed


if __name__ == "__main__":
    print(
        "Схема маршрутов обновлена."
        if migrate_database()
        else "Схема маршрутов уже обновлена."
    )
