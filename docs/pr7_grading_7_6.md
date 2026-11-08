# ПР7: таблица оценивания 7.6 для проекта доставки

Таблица соответствует новой редакции раздела 7.6 методички: 25 показателей, за индивидуальный проект можно получить до 1,5 балла. Формулировки ниже привязаны к проекту **«Система планирования маршрутов доставки»**. На защите показывайте соответствующий файл и, где указано, страницу сайта. [Чек-лист 7.2](pr7_checklist.md) содержит карту технических требований.

| № | Показатель и вопрос для защиты | Где показать и что ответить |
| ---: | --- | --- |
| 1 | **Проектирование структуры БД.** Какие таблицы, данные и связи есть в проекте? | [README](../README.md) — таблица структуры; [schema.sql](../sql/schema.sql) — реальные определения. `clients`, `couriers`, `orders`, `routes`, `route_orders`, `courier_bookings`. Курьер маршрута определяется через связанные заказы. |
| 2 | **Создание таблиц и связей.** Зачем нужны PK и FK? | [schema.sql](../sql/schema.sql): `PRIMARY KEY` отличает записи, `REFERENCES` связывает заказ с клиентом/курьером, а `route_orders` — заказ с маршрутом. В [database.py](../db/database.py) включается проверка FK. |
| 3 | **Создание базы и выполнение схемы.** Как создать SQLite и повторить запуск? | [import_json.py](../db/import_json.py) вызывает схему из [schema.sql](../sql/schema.sql). `CREATE TABLE IF NOT EXISTS` позволяет повторно выполнить скрипт без ошибки «table already exists». Команда: `python -m db.import_json`. |
| 4 | **Подключение к БД.** Как проверить, что используется нужный файл? | [database.py](../db/database.py): `DATABASE_PATH`, `current_database_path()`, `sqlite3.connect()` и `fetch_one("overview_counts")`. Предметная база — [data/delivery.sqlite](../data/delivery.sqlite), служебная Django — `db.sqlite3`. |
| 5 | **Импорт JSON.** Почему важен порядок вставки? | [import_json.py](../db/import_json.py) читает `data/*.json` и сначала вставляет клиентов и курьеров, затем заказы, маршруты и связи. Иначе FK ссылались бы на ещё не созданные записи. |
| 6 | **Проверка импорта.** Как обнаружить пропущенные данные? | [test_database.py](../tests/test_database.py) сравнивает количества строк с JSON: `3/3/4/2/2`, проверяет брони и `PRAGMA foreign_key_check`. Подсчёт вручную: `SELECT COUNT(*) FROM orders;`. |
| 7 | **SELECT.** Как получить список заказов и изменить набор полей? | `orders_list` в [queries.sql](../sql/queries.sql). Уберите, например, `o.weight` из `SELECT`: столбец пропадёт из результата и станет недоступен шаблону. |
| 8 | **WHERE.** Как изменить условие отбора? | `orders_by_status_filter` в [queries.sql](../sql/queries.sql): `WHERE o.status = ?`. Передайте `создан` или `назначен`; состав результата поменяется. |
| 9 | **Фильтр по состоянию.** Какие заказы считаются действующими? | `active_orders` в [queries.sql](../sql/queries.sql) выбирает статусы `создан` и `назначен`, исключая `отменён` и `доставлен`. Выберите «Активные» на `/orders/`. |
| 10 | **JOIN.** Как получить сведения из связанных таблиц? | `orders_list` в [queries.sql](../sql/queries.sql): `JOIN clients ON c.id = o.client_id` и `LEFT JOIN couriers ON u.id = o.courier_id`. `LEFT JOIN` сохраняет заказ без назначенного курьера. |
| 11 | **Несколько условий.** Как повлияет изменение одного из них? | `available_couriers` в [queries.sql](../sql/queries.sql) проверяет активность, грузоподъёмность, дату и отсутствие действующей брони. На `/bookings/available/` смените дату или заказ: список свободных курьеров изменится. |
| 12 | **COUNT().** Что будет, если подходящих строк нет? | `overview_counts`, `booking_metrics` в [queries.sql](../sql/queries.sql): `COUNT(*)` считает строки и возвращает `0` на пустой таблице. `courier_workload` использует `COUNT(o.id)`, чтобы курьер без заказов получил `0`. |
| **13** | **GROUP BY.** Как формируются группы? | `orders_by_status` в [queries.sql](../sql/queries.sql) создаёт по одной строке на каждый статус и считает заказы/вес внутри группы. `courier_workload` создаёт группу на каждого курьера. Результат виден на `/statistics/`. |
| **14** | **HAVING.** Как изменить порог и чем он отличается от WHERE? | `busy_couriers` в [queries.sql](../sql/queries.sql): условие статуса в `JOIN` ограничивает исходные заказы до группировки, а `HAVING COUNT(o.id) > 0` после группировки оставляет занятых курьеров. Если заменить `> 0` на `> 1`, при текущих данных список будет пустым. |
| **15** | **Параметризованный SQL.** Как безопасно передать пользовательское значение? | `/orders/?status=создан` → [delivery_orders/views.py](../delivery_orders/views.py) → `fetch_all("orders_by_status_filter", (status,))` в [database.py](../db/database.py) → `WHERE o.status = ?` в [queries.sql](../sql/queries.sql). `sqlite3` связывает значение с `?` отдельно от текста SQL, поэтому ввод не превращается в SQL-код. |
| 16 | **Получение результатов SQL.** Как прочитать поля по имени? | [database.py](../db/database.py) задаёт `db.row_factory = sqlite3.Row`; [delivery_orders/views.py](../delivery_orders/views.py) использует `row["status"]` и `dict(row)`. |
| 17 | **Список объектов.** Как данные попадают на страницу? | `/orders/`: [views.py](../delivery_orders/views.py) вызывает запрос `orders_page`, передаёт `orders` в [order_list.html](../delivery_orders/templates/delivery_orders/order_list.html). |
| 18 | **Отфильтрованные записи.** Что определяет состав страницы? | На `/orders/?status=создан` [представление](../delivery_orders/views.py) передаёт статус в `orders_by_status_filter`; SQL `WHERE` оставляет только подходящие строки. |
| 19 | **Связанные данные.** Как результат JOIN формирует страницу? | На `/orders/` видны заказ, клиент и курьер. Поля `client_name` и `courier_name` приходят из `orders_list`/`orders_page` в [queries.sql](../sql/queries.sql) и выводятся в [шаблоне](../delivery_orders/templates/delivery_orders/order_list.html). |
| 20 | **Поиск по параметрам.** Как значение из формы доходит до SQL? | `/orders/?q=Мира`: [views.py](../delivery_orders/views.py) читает `request.GET`, `search_orders()` в [database.py](../db/database.py) экранирует шаблон `LIKE` и вызывает `orders_search` с параметрами. |
| 21 | **Статистика.** Как агрегаты доходят до шаблона? | [homepage/views.py](../homepage/views.py) вызывает `order_metrics`, `orders_by_status`, `courier_workload`, `busy_couriers`; [statistics.html](../homepage/templates/homepage/statistics.html) показывает результат на `/statistics/`. |
| 22 | **Передача в шаблон.** Что проверить, если SQL вернул строки, а страница пуста? | Сравните ключ `"statuses"` в [homepage/views.py](../homepage/views.py) с `{% for row in statuses %}` в [statistics.html](../homepage/templates/homepage/statistics.html). При несовпадении исправляют имя ключа или переменной шаблона. |
| 23 | **Пустой результат.** Чем он отличается от ошибки SQL? | На `/orders/?q=несуществующий-адрес` запрос успешно возвращает пустой список, а [order_list.html](../delivery_orders/templates/delivery_orders/order_list.html) показывает сообщение через `{% empty %}`. Ошибка SQL прерывает выполнение запроса. |
| 24 | **Диагностика SQL.** Как найти неверное поле или условие JOIN? | Сверьте `o.client_id` и `c.id` в `orders_list` из [queries.sql](../sql/queries.sql) со схемой [schema.sql](../sql/schema.sql). Выполните запрос в SQLite, сравните результат с `/orders/`; исправление условия `JOIN` меняет связанные имена в выдаче. |
| 25 | **Сквозная обработка Django-запроса.** Где искать ошибку? | `/orders/?status=создан`: [URL](../delivery_orders/urls.py) → [view](../delivery_orders/views.py) → [db/database.py](../db/database.py) → `orders_by_status_filter` в [queries.sql](../sql/queries.sql) → [шаблон](../delivery_orders/templates/delivery_orders/order_list.html). Проверяйте параметр, результат SQL, контекст и вывод по очереди. |

## Быстрая демонстрация вопросов 13–15

1. Откройте [queries.sql](../sql/queries.sql) на `orders_by_status` и страницу `/statistics/`: каждый статус — отдельная группа `GROUP BY`.
2. Ниже покажите `busy_couriers`: `HAVING COUNT(o.id) > 0` оставляет группы с назначенными заказами. Для демонстрации порога выполните этот же запрос с `> 1`: при текущих данных строк не будет.
3. Откройте `/orders/?status=создан` и покажите цепочку `request.GET` → кортеж `(status,)` → `db.execute(sql, parameters)` → `WHERE o.status = ?`. Значение передаётся отдельно от SQL.

### Вопрос 15: параметризованный запрос

На защите можно пройти по трём участкам кода:

1. В [order_list()](../delivery_orders/views.py) `request.GET.get("status", "")` получает строку из адреса `/orders/?status=создан`. Представление проверяет, что такой статус разрешён, и вызывает `fetch_all("orders_by_status_filter", (status,))`. Запятая нужна для кортежа из одного значения.
2. В [queries.sql](../sql/queries.sql) текст запроса постоянный: `WHERE o.status = ?`. `?` обозначает место значения, выбранного пользователем. Тот же запрос подходит для статусов `создан`, `назначен` и других разрешённых статусов.
3. В [database.py](../db/database.py) вызов `db.execute(queries()[name], parameters)` передаёт SQL и значения раздельно. Драйвер SQLite связывает `?` с первым элементом кортежа как со значением для сравнения и возвращает подходящие строки.

**Почему нельзя собирать SQL из ввода:** при вставке строки через f-строку или конкатенацию символ `'` может закрыть строковый литерал, а остаток ввода изменить условие запроса. Например, `создан' OR 1=1 --` при ошибочной сборке SQL мог бы превратить фильтр в условие, истинное для всех заказов. При передаче через `?` вся эта строка остаётся одним значением статуса, которому не соответствует ни одна запись. Проверка допустимых статусов в представлении полезна дополнительно, но не заменяет параметризацию.

Короткий ответ преподавателю: «Значение `status` я беру из `request.GET` и передаю в SQLite отдельным кортежем `(status,)`. В самом SQL стоит `WHERE o.status = ?`. SQLite воспринимает параметр как значение, а не как часть команды, поэтому пользовательский ввод не может изменить запрос».

#### Весь путь от выбора статуса до браузера

Для демонстрации откройте `/orders/?status=создан` и показывайте файлы в таком порядке:

1. [order_list.html](../delivery_orders/templates/delivery_orders/order_list.html): форма с `method="get"` и полем `name="status"` отправляет выбранное значение браузером на `/orders/`.
2. [delivery_planner/urls.py](../delivery_planner/urls.py) передаёт путь `/orders/` в [delivery_orders/urls.py](../delivery_orders/urls.py), где `path("", views.order_list, name="list")` вызывает функцию `order_list(request)`. Часть `?status=создан` находится в `request.GET` и не меняет выбор URL.
3. [delivery_orders/views.py](../delivery_orders/views.py): функция читает `status`, проверяет допустимость и вызывает `fetch_all("orders_by_status_filter", (status,))`. Здесь указан **идентификатор запроса**, а не сам текст SQL.
4. [db/database.py](../db/database.py): `queries()` читает [sql/queries.sql](../sql/queries.sql) и находит текст под меткой `-- name: orders_by_status_filter`. `connection()` открывает `data/delivery.sqlite`, а `db.execute(queries()[name], parameters)` запускает `SELECT ... WHERE o.status = ?`, передав `status` отдельным значением.
5. `fetchall()` возвращает строки `sqlite3.Row` из SQLite обратно в `order_list()`. В `render(request, "delivery_orders/order_list.html", {"orders": [dict(row) for row in orders], ...})` строки становятся контекстом шаблона.
6. [order_list.html](../delivery_orders/templates/delivery_orders/order_list.html) перебирает `orders`; [order_row.html](../delivery_orders/templates/delivery_orders/includes/order_row.html) выводит поля заказа в HTML-строку. `render()` возвращает Django объект `HttpResponse` с готовым HTML, а сервер отправляет HTTP-ответ в браузер.

Краткая схема: **браузер → URL → `order_list()` → `fetch_all()` → SQLite-запрос → `fetchall()` → `render()` → HTML → браузер**. В браузер отправляется HTML-страница, а не текст SQL или соединение с базой.
