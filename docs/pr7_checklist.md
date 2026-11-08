# ПР7: где показать пункты чек-листа 7.2

Номера соответствуют разделу **«7.2. Чек-лист выполнения индивидуального проекта»**. Формулировки про помещения и бронирования адаптированы к системе доставки: вместо помещения здесь курьер, вместо бронирования помещения — резервирование курьера для заказа на дату. Откройте нужный файл из таблицы; в ключевых местах кода есть комментарии `ПР7, 7.2 №…`.

| № | Требование чек-листа | Где показать в этом проекте |
| ---: | --- | --- |
| 1 | Проект ПР1–ПР6 сохранён и продолжен | [README](../README.md), [консольная версия](../main.py), [JSON-хранилище](../storage.py), приложения `homepage/`, `delivery_orders/`, `delivery_routes/`. |
| 2 | Определены сущности предметной области | Клиент, курьер, заказ, маршрут и бронь курьера: [README](../README.md), [модели](../models/), [схема](../sql/schema.sql). |
| 3 | Определены таблицы | Шесть `CREATE TABLE` в [schema.sql](../sql/schema.sql): `clients`, `couriers`, `orders`, `routes`, `route_orders`, `courier_bookings`. |
| 4 | Определены поля и типы данных | Столбцы с `INTEGER`, `REAL`, `TEXT` в [schema.sql](../sql/schema.sql); сводная таблица в [README](../README.md). |
| 5 | Определены первичные ключи | `PRIMARY KEY` в [schema.sql](../sql/schema.sql), в том числе составной ключ `route_orders`. |
| 6 | Определены необходимые внешние ключи | `REFERENCES` в [schema.sql](../sql/schema.sql): заказы → клиенты/курьеры, `route_orders` → маршруты/заказы, брони → заказы/курьеры. Курьер маршрута определяется через его заказы; отдельного FK `routes.courier_id` нет. |
| 7 | Создан файл базы данных SQLite | [data/delivery.sqlite](../data/delivery.sqlite); путь `DATABASE_PATH` в [database.py](../db/database.py). |
| 8 | Таблицы созданы средствами SQL | [schema.sql](../sql/schema.sql); вызов `db.executescript(schema)` в [import_json.py](../db/import_json.py). Старая таблица маршрутов обновляется через [migrate_routes.py](../db/migrate_routes.py). |
| 9 | Создан модуль подключения | [db/database.py](../db/database.py), функция `connection()`. |
| 10 | Включена проверка внешних ключей | `PRAGMA foreign_keys = ON` в [database.py](../db/database.py); проверка ограничений в [test_database.py](../tests/test_database.py). |
| 11 | Создан скрипт переноса данных | [db/import_json.py](../db/import_json.py); запуск `python -m db.import_json`. Миграция прежней структуры — [db/migrate_routes.py](../db/migrate_routes.py). |
| 12 | Данные перенесены из JSON-файлов | Исходные [JSON-файлы](../data/) и команды `INSERT` в [import_json.py](../db/import_json.py); результат — [delivery.sqlite](../data/delivery.sqlite). |
| 13 | Импортированные данные проверены | [test_database.py](../tests/test_database.py): повторный импорт с сохранением брони, числа исходных записей `3/3/4/2/2`, `PRAGMA foreign_key_check`. |
| 14 | Создан файл запросов | [sql/queries.sql](../sql/queries.sql), 23 именованных запроса. |
| 15 | Запросы проверены в SQLite CLI | В корне проекта: `sqlite3 data/delivery.sqlite ".read sql/queries.sql"`. Команда выполнена без ошибок; параметризованные варианты отдельно проверяет [test_database.py](../tests/test_database.py). |
| 16 | Использованы `SELECT` и `WHERE` | `orders_list`, `order_detail`, `orders_search`, `orders_by_status_filter` в [queries.sql](../sql/queries.sql); [представление заказов](../delivery_orders/views.py). |
| 17 | Использован `JOIN` | `orders_list`, `routes_list`, `route_orders` в [queries.sql](../sql/queries.sql); `routes_list` получает курьера цепочкой `routes → route_orders → orders → couriers`. |
| 18 | Использованы агрегатные функции | `overview_counts` (`COUNT`) и `order_metrics` (`COUNT`, `AVG`, `SUM`) в [queries.sql](../sql/queries.sql); [главная и статистика](../homepage/views.py). |
| 19 | Выполнена группировка `GROUP BY` | `routes_list`, `orders_by_status`, `courier_workload`, `busy_couriers` в [queries.sql](../sql/queries.sql). |
| 20 | Выполнена фильтрация групп `HAVING` | `busy_couriers` в [queries.sql](../sql/queries.sql), результат в [статистике](../homepage/templates/homepage/statistics.html). |
| 21 | Значения передаются параметрами `?` | Плейсхолдеры в [queries.sql](../sql/queries.sql), `execute(query, parameters)` и подготовка поиска в [database.py](../db/database.py), ID/статус из [views.py](../delivery_orders/views.py). |
| 22 | Использован `sqlite3.Row` в представлениях | `db.row_factory = sqlite3.Row` в [database.py](../db/database.py); представления [заказов](../delivery_orders/views.py), [маршрутов](../delivery_routes/views.py) и [статистики](../homepage/views.py) получают строки и передают их поля шаблонам. |
| 23 | Список заказов выводится из SQLite (аналог списка помещений) | `/orders/`: [SQL](../sql/queries.sql) `orders_page` → [view](../delivery_orders/views.py) → [шаблон](../delivery_orders/templates/delivery_orders/order_list.html). |
| 24 | Список бронирований курьеров выводится из SQLite | Бронь курьера для заказа на дату: [SQL](../sql/queries.sql) `bookings_list` → [view](../delivery_bookings/views.py) → [шаблон](../delivery_bookings/templates/delivery_bookings/booking_list.html), `/bookings/`. |
| 25 | Поиск свободных курьеров по дате (аналог поиска помещений) | Свободные курьеры на дату с учётом веса заказа: [SQL](../sql/queries.sql) `available_couriers` → [db/bookings.py](../db/bookings.py) → [view](../delivery_bookings/views.py) → [шаблон](../delivery_bookings/templates/delivery_bookings/available.html), `/bookings/available/`. |
| 26 | Реализована страница статистики | `/statistics/` показывает статистику заказов, курьеров и броней: [view](../homepage/views.py), [шаблон](../homepage/templates/homepage/statistics.html), [SQL](../sql/queries.sql) `booking_metrics`, `bookings_by_courier`. |
| 27 | Настроена навигация между разделами | [navigation.html](../templates/includes/navigation.html) и именованные адреса в [homepage/urls.py](../homepage/urls.py), [delivery_orders/urls.py](../delivery_orders/urls.py), [delivery_routes/urls.py](../delivery_routes/urls.py), [delivery_bookings/urls.py](../delivery_bookings/urls.py). |
| 28 | Обновлён README.md | [README](../README.md): структура, ключи, импорт, запросы, страницы, запуск и проверки. |
| 29 | Выполнены проверки проекта | [test_database.py](../tests/test_database.py) и [test_web.py](../tests/test_web.py). Команды: `python manage.py check`, `python -m pytest -q`, `python -m flake8 . --extend-exclude=venv,.venv,.pr5-deps`. |
| 30 | Изменения сохранены в Git с меткой `PR7:` | **Ожидает повторного коммита.** Для просмотра изменений в PyCharm два локальных коммита возвращены в рабочую копию; после проверки сохраните их коммитом с префиксом `PR7:`. |
| 31 | Не менее 10 запросов и двух каждого вида | [queries.sql](../sql/queries.sql): списки `clients_list`, `couriers_list`; `WHERE` `order_detail`, `route_detail`; `JOIN` `orders_list`, `routes_list`; агрегаты `overview_counts`, `order_metrics`; `GROUP BY` `orders_by_status`, `courier_workload`. Все запросы запускает [test_database.py](../tests/test_database.py). |

## Быстрая проверка перед демонстрацией

```powershell
sqlite3 data/delivery.sqlite ".tables"
sqlite3 data/delivery.sqlite "PRAGMA foreign_key_check;"
sqlite3 data/delivery.sqlite ".read sql/queries.sql"
python manage.py check
python -m pytest -q
python -m flake8 . --extend-exclude=venv,.venv,.pr5-deps
git status --short
```

Для примера параметризованного поиска откройте `/orders/?q=Мира`; для `HAVING` — `/statistics/`, блок «Курьеры с назначенными заказами». Для адаптации бронирования откройте `/bookings/available/`, выберите дату и заказ #3, забронируйте Алексея, затем покажите запись на `/bookings/` и агрегат на `/statistics/`.
