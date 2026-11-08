"""ПР7, 7.6 №5: перенос исходных JSON-файлов в предметную SQLite.

Порядок: прочитать JSON, создать таблицы из schema.sql, вставить записи
по зависимостям внешних ключей и проверить связи.
Запуск: python -m db.import_json.
"""

import sqlite3
from pathlib import Path

from storage import load_records

from db.database import BASE_DIR, connection, current_database_path
from db.migrate_routes import migrate_routes_without_courier


def _validate_routes(routes: list[dict], orders: list[dict]) -> None:
    """Проверить, что курьер маршрута однозначно определяется по заказам."""
    orders_by_id = {order["id"]: order for order in orders}
    routed_orders: set[int] = set()
    for route in routes:
        order_ids = route["order_ids"]
        if not order_ids:
            raise ValueError(f"Маршрут #{route['id']} не содержит заказов.")
        courier_ids = set()
        for order_id in order_ids:
            order = orders_by_id.get(order_id)
            if order is None or order.get("courier_id") is None:
                raise ValueError(
                    f"Заказ #{order_id} маршрута #{route['id']} "
                    "не найден или не имеет курьера."
                )
            if order_id in routed_orders:
                raise ValueError(
                    f"Заказ #{order_id} включён в несколько маршрутов."
                )
            routed_orders.add(order_id)
            courier_ids.add(order["courier_id"])
        if len(courier_ids) != 1:
            raise ValueError(
                f"В маршруте #{route['id']} заказы разных курьеров."
            )
        legacy_courier = route.get("courier_id")
        if legacy_courier is not None and legacy_courier not in courier_ids:
            raise ValueError(
                f"В маршруте #{route['id']} прежний courier_id "
                "не совпадает с курьером заказов."
            )


def import_data(
    data_dir: Path = BASE_DIR / "data", db_path: Path | None = None
) -> None:
    """Обновить исходные таблицы из JSON, сохранив бронирования."""
    # №5: storage.load_records читает списки словарей из четырёх JSON-файлов.
    # Это исходные данные консольного проекта; Django читает уже SQLite.
    clients = load_records(data_dir / "clients.json")
    couriers = load_records(data_dir / "couriers.json")
    orders = load_records(data_dir / "orders.json")
    routes = load_records(data_dir / "routes.json")
    _validate_routes(routes, orders)
    # №1 и №5: схема содержит CREATE TABLE и ограничения, а не сами записи.
    schema = (BASE_DIR / "sql" / "schema.sql").read_text(encoding="utf-8")
    db_path = db_path if db_path is not None else current_database_path()
    # Создаём каталог data/, если импорт запускается в новом окружении.
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with connection(db_path) as db:
        # Старую SQLite с routes.courier_id перестраиваем без потери строк.
        migrate_routes_without_courier(db)
        # №1 и №2: выполняем SQL из schema.sql в файле delivery.sqlite.
        # IF NOT EXISTS позволяет запускать создание схемы повторно.
        db.executescript(schema)
        # №5: замена данных проходит в транзакции: ошибка INSERT откатит её.
        with db:
            # BEGIN IMMEDIATE запрещает конкурентную запись до конца импорта.
            db.execute("BEGIN IMMEDIATE")
            # Брони созданы на сайте, а не в JSON: временно запоминаем их,
            # чтобы повторный импорт не стирал введённые пользователем даты.
            bookings = db.execute(
                "SELECT id, order_id, courier_id, delivery_date, is_cancelled "
                "FROM courier_bookings ORDER BY id"
            ).fetchall()
            # Сначала очищаем дочерние таблицы, затем родительские: иначе
            # FK не разрешили бы удалить заказ с существующей бронью.
            for table in (
                "courier_bookings",
                "route_orders",
                "routes",
                "orders",
                "couriers",
                "clients",
            ):
                db.execute(f"DELETE FROM {table}")
            # Вставляем родителей раньше детей: clients/couriers, затем
            # orders/routes, затем связи route_orders и сохранённые брони.
            # executemany выполняет один шаблон INSERT для множества записей.
            db.executemany(
                "INSERT INTO clients (id, name, phone) VALUES (?, ?, ?)",
                [
                    (item["id"], item["name"], item["phone"])
                    for item in clients
                ],
            )
            db.executemany(
                "INSERT INTO couriers (id, name, capacity, active) "
                "VALUES (?, ?, ?, ?)",
                [
                    (
                        item["id"],
                        item["name"],
                        item["capacity"],
                        int(item["active"]),
                    )
                    for item in couriers
                ],
            )
            db.executemany(
                "INSERT INTO orders "
                "(id, destination, weight, client_id, courier_id, status) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (
                        item["id"],
                        item["destination"],
                        item["weight"],
                        item["client_id"],
                        item.get("courier_id"),
                        item["status"],
                    )
                    for item in orders
                ],
            )
            db.executemany(
                "INSERT INTO routes (id, status) VALUES (?, ?)",
                [
                    (item["id"], item["status"])
                    for item in routes
                ],
            )
            db.executemany(
                "INSERT INTO route_orders (route_id, order_id) VALUES (?, ?)",
                [
                    (route["id"], order_id)
                    for route in routes
                    for order_id in route["order_ids"]
                ],
            )
            db.executemany(
                "INSERT INTO courier_bookings "
                "(id, order_id, courier_id, delivery_date, is_cancelled) "
                "VALUES (?, ?, ?, ?, ?)",
                [tuple(row) for row in bookings],
            )
            # №4–5: проверяем все ссылки в готовой базе. Если заказ/курьер
            # из брони удалён из JSON, восстановление выше вызовет ошибку FK,
            # а транзакция оставит прежние данные нетронутыми.
            violations = db.execute("PRAGMA foreign_key_check").fetchall()
            if violations:
                raise sqlite3.IntegrityError(
                    f"Нарушены внешние ключи: {violations}"
                )


if __name__ == "__main__":
    # Запуск модуля импортирует JSON и печатает путь к заполненной SQLite.
    import_data()
    print(f"Данные импортированы в {current_database_path()}")
