"""ПР7, 7.6 №1 и №4: путь к предметной SQLite, подключение и SELECT.

Структура таблиц: sql/schema.sql; запросы: sql/queries.sql.
Импорт: db/import_json.py.
Бронирование и отмена брони: db/bookings.py. Django ORM здесь не применяется.
"""

import os
import sqlite3
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import Iterator

# №1: берём корень проекта относительно этого файла, чтобы не зависеть от
# каталога, из которого запущены manage.py, тесты или модуль импорта.
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "data" / "delivery.sqlite"
QUERIES_PATH = BASE_DIR / "sql" / "queries.sql"


def current_database_path() -> Path:
    """База проекта; путь можно переопределить для изолированных проверок."""
    return Path(os.environ.get("DELIVERY_DB_PATH", DATABASE_PATH))


@contextmanager
def connection(path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Открыть SQLite, включить проверку FK и закрыть соединение."""
    # №1: sqlite3.connect открывает файл базы; если файла нет, SQLite его
    # создаст. Таблицы затем создаёт import_json.py из schema.sql.
    db = sqlite3.connect(path if path is not None else current_database_path())
    # sqlite3.Row позволяет читать столбцы по имени: row["name"], а не row[1].
    db.row_factory = sqlite3.Row
    # №4: в SQLite проверка внешних ключей включается для КАЖДОГО соединения.
    # После этого ссылка на несуществующий client_id/courier_id вызывает
    # sqlite3.IntegrityError; пример есть в tests/test_database.py.
    db.execute("PRAGMA foreign_keys = ON")
    try:
        yield db
    finally:
        # finally закрывает соединение даже при ошибке SQL-запроса.
        db.close()


@lru_cache(maxsize=1)
def queries() -> dict[str, str]:
    """Разделить queries.sql по меткам '-- name:' на запросы по имени."""
    # ПР7, 7.6 №15 и №25: имя orders_by_status_filter соответствует метке
    # в sql/queries.sql. View передаёт имя, а отсюда берётся текст SELECT.
    result: dict[str, str] = {}
    name = None
    lines: list[str] = []
    for line in QUERIES_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith("-- name: "):
            if name is not None:
                result[name] = "\n".join(lines).strip()
            name = line.removeprefix("-- name: ").strip()
            lines = []
        elif name is not None and not line.startswith("--"):
            lines.append(line)
    if name is not None:
        result[name] = "\n".join(lines).strip()
    return result


def fetch_all(
    name: str, parameters: tuple = (), path: Path | None = None
) -> list[sqlite3.Row]:
    """Выполнить параметризованный SELECT и вернуть все строки."""
    with connection(path) as db:
        # ПР7, таблица 7.6 №15, шаг 3: queries()[name] — готовый SQL из
        # sql/queries.sql, а parameters — отдельный кортеж значений из view.
        # sqlite3 связывает первый ? с первым элементом кортежа и т. д.
        # Значение "создан" сравнивается с o.status как данные, а не как SQL.
        # Если склеить ввод с SQL через f-строку, кавычка в нём может закрыть
        # строковый литерал, а последующий текст изменить условие WHERE.
        # Например, ввод "создан' OR 1=1 --" при таком склеивании мог бы
        # выбрать все заказы. С ? он остаётся одним значением и не совпадёт
        # ни с одним статусом. Параметры заменяют значения, не имена таблиц.
        # SELECT выполняется в локальном файле data/delivery.sqlite.
        # fetchall() возвращает строки sqlite3.Row обратно в order_list().
        return db.execute(queries()[name], parameters).fetchall()


def fetch_one(
    name: str, parameters: tuple = (), path: Path | None = None
) -> sqlite3.Row | None:
    """Выполнить параметризованный SELECT и вернуть одну строку."""
    with connection(path) as db:
        return db.execute(queries()[name], parameters).fetchone()


def search_orders(term: str, status: str = "") -> list[sqlite3.Row]:
    """Искать заказы, считая ввод текстом, а не маской LIKE."""
    escaped = (
        term.strip()
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )
    pattern = f"%{escaped}%"
    if status:
        return fetch_all(
            "orders_search_status", (status, pattern, pattern, pattern)
        )
    return fetch_all("orders_search", (pattern, pattern, pattern))
