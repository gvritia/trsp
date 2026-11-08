-- ПР7, 7.6 №1: sql/queries.sql хранит SELECT-запросы, но не создаёт таблицы.
-- Структура таблиц находится в sql/schema.sql, а файл БД — data/delivery.sqlite.
-- db/database.py читает запрос по метке '-- name:' и выполняет его через sqlite3.
-- ПР7, чек-лист 7.2, №14, №16–21 и №31: каталог SQL-запросов.
-- №15: проверить все запросы командой sqlite3 data/delivery.sqlite ".read sql/queries.sql".
-- Параметризованные примеры дополнительно проверяются в tests/test_database.py.
-- name: clients_list
-- Список клиентов (SELECT 1).
SELECT id, name, phone FROM clients ORDER BY id;

-- name: couriers_list
-- Список курьеров (SELECT 2).
SELECT id, name, capacity, active FROM couriers ORDER BY id;

-- name: orders_list
-- Заказы с клиентом и курьером (JOIN 1).
SELECT o.id, o.destination, o.weight, o.status,
       c.name AS client_name, c.phone AS client_phone,
       u.name AS courier_name
FROM orders AS o
JOIN clients AS c ON c.id = o.client_id
LEFT JOIN couriers AS u ON u.id = o.courier_id
ORDER BY o.id;

-- name: routes_list
-- Курьер маршрута находится через его заказы (JOIN 2, GROUP BY 1).
SELECT r.id, r.status, c.name AS courier_name,
       COUNT(ro.order_id) AS order_count
FROM routes AS r
LEFT JOIN route_orders AS ro ON ro.route_id = r.id
LEFT JOIN orders AS o ON o.id = ro.order_id
LEFT JOIN couriers AS c ON c.id = o.courier_id
GROUP BY r.id, r.status, c.name
ORDER BY r.id;

-- name: order_detail
-- Заказ по ID (WHERE 1).
SELECT o.id, o.destination, o.weight, o.status,
       c.name AS client_name, c.phone AS client_phone,
       u.name AS courier_name
FROM orders AS o
JOIN clients AS c ON c.id = o.client_id
LEFT JOIN couriers AS u ON u.id = o.courier_id
WHERE o.id = ?;

-- name: route_detail
-- Маршрут по ID (WHERE 2).
SELECT r.id, r.status, c.name AS courier_name
FROM routes AS r
LEFT JOIN route_orders AS ro ON ro.route_id = r.id
LEFT JOIN orders AS o ON o.id = ro.order_id
LEFT JOIN couriers AS c ON c.id = o.courier_id
WHERE r.id = ?
GROUP BY r.id, r.status, c.name;

-- name: route_orders
-- Заказы конкретного маршрута (JOIN 3).
SELECT o.id, o.destination
FROM route_orders AS ro JOIN orders AS o ON o.id = ro.order_id
WHERE ro.route_id = ? ORDER BY o.id;

-- name: orders_search
-- Поиск по адресу, клиенту или курьеру; параметр содержит шаблон LIKE.
SELECT o.id, o.destination, o.weight, o.status,
       c.name AS client_name, u.name AS courier_name
FROM orders AS o
JOIN clients AS c ON c.id = o.client_id
LEFT JOIN couriers AS u ON u.id = o.courier_id
WHERE o.destination LIKE ? ESCAPE '\' COLLATE NOCASE
   OR c.name LIKE ? ESCAPE '\' COLLATE NOCASE
   OR u.name LIKE ? ESCAPE '\' COLLATE NOCASE
ORDER BY o.id;

-- name: orders_by_status_filter
-- ПР7, таблица 7.6 №15: статус выбран пользователем на /orders/.
-- WHERE o.status = ? означает «сравнить столбец со значением параметра».
-- Знак ? не содержит значение сам: views.py передаёт (status,) в fetch_all,
-- а database.py вызывает db.execute(этот_SQL, (status,)).
-- Для status = 'создан' вернутся только созданные заказы. Для другого
-- допустимого статуса тот же SQL работает без изменения текста запроса.
-- Не пишите WHERE o.status = ' + ввод + ': кавычка из ввода может нарушить
-- синтаксис или изменить условие. При ? весь ввод остаётся одним значением.
SELECT o.id, o.destination, o.weight, o.status,
       c.name AS client_name, u.name AS courier_name
FROM orders AS o
JOIN clients AS c ON c.id = o.client_id
LEFT JOIN couriers AS u ON u.id = o.courier_id
WHERE o.status = ? ORDER BY o.id;

-- name: orders_search_status
-- Совмещённые поиск и фильтр по статусу.
SELECT o.id, o.destination, o.weight, o.status,
       c.name AS client_name, u.name AS courier_name
FROM orders AS o
JOIN clients AS c ON c.id = o.client_id
LEFT JOIN couriers AS u ON u.id = o.courier_id
WHERE o.status = ?
  AND (o.destination LIKE ? ESCAPE '\' COLLATE NOCASE
       OR c.name LIKE ? ESCAPE '\' COLLATE NOCASE
       OR u.name LIKE ? ESCAPE '\' COLLATE NOCASE)
ORDER BY o.id;

-- name: overview_counts
-- Общие количества (агрегат 1).
SELECT (SELECT COUNT(*) FROM clients) AS client_count,
       (SELECT COUNT(*) FROM couriers) AS courier_count,
       (SELECT COUNT(*) FROM orders) AS order_count,
       (SELECT COUNT(*) FROM routes) AS route_count;

-- name: order_metrics
-- Показатели заказов (агрегат 2).
SELECT COUNT(*) AS total_orders,
       COALESCE(ROUND(AVG(weight), 1), 0) AS average_weight,
       COALESCE(ROUND(100.0 * SUM(CASE WHEN status = 'назначен' THEN 1 ELSE 0 END)
           / NULLIF(SUM(CASE WHEN status NOT IN ('отменён', 'доставлен') THEN 1 ELSE 0 END), 0), 1), 0) AS efficiency
FROM orders;

-- name: orders_by_status
-- ПР7, таблица 7.6 №13: GROUP BY собирает заказы с одним status в группу.
-- COUNT(*) и SUM(weight) считаются отдельно внутри каждой группы;
-- результат содержит одну строку на статус, а не одну строку на заказ.
SELECT status, COUNT(*) AS order_count, ROUND(SUM(weight), 1) AS total_weight
FROM orders GROUP BY status ORDER BY status;

-- name: courier_workload
-- ПР7, таблица 7.6 №13: GROUP BY создаёт одну группу на курьера.
-- LEFT JOIN сохраняет курьеров без назначенных заказов; COUNT(o.id) даёт им 0.
SELECT c.id, c.name, c.capacity, c.active,
       COUNT(o.id) AS order_count,
       COALESCE(ROUND(SUM(o.weight), 1), 0) AS total_weight
FROM couriers AS c
LEFT JOIN orders AS o ON o.courier_id = c.id AND o.status = 'назначен'
GROUP BY c.id, c.name, c.capacity, c.active ORDER BY c.id;

-- name: busy_couriers
-- ПР7, таблица 7.6 №14; чек-лист 7.2 №19–20: HAVING фильтрует группы.
-- Условие o.status = 'назначен' в JOIN учитывает только нужные исходные заказы.
-- GROUP BY собирает строки по курьерам; затем HAVING COUNT(o.id) > 0
-- убирает курьеров без назначенных заказов. WHERE проверял бы отдельные
-- строки ДО группировки и не мог бы проверить результат COUNT для группы.
-- Для защиты поменяйте порог на > 1 в копии запроса: в исходных данных у
-- каждого занятого курьера по одному заказу, поэтому строк не останется.
SELECT c.name, COUNT(o.id) AS assigned_orders
FROM couriers AS c
LEFT JOIN orders AS o ON o.courier_id = c.id AND o.status = 'назначен'
GROUP BY c.id, c.name
HAVING COUNT(o.id) > 0
ORDER BY c.name;

-- name: orders_page
-- ПР7, чек-лист 7.2 №16: страница списка заказов через LIMIT/OFFSET.
SELECT o.id, o.destination, o.weight, o.status,
       c.name AS client_name, c.phone AS client_phone,
       u.name AS courier_name
FROM orders AS o
JOIN clients AS c ON c.id = o.client_id
LEFT JOIN couriers AS u ON u.id = o.courier_id
ORDER BY o.id LIMIT ? OFFSET ?;

-- name: active_orders
-- ПР7, таблица 7.6 №9: оба действующих статуса одним запросом.
SELECT o.id, o.destination, o.weight, o.status,
       c.name AS client_name, u.name AS courier_name
FROM orders AS o JOIN clients AS c ON c.id = o.client_id
LEFT JOIN couriers AS u ON u.id = o.courier_id
WHERE o.status IN ('создан', 'назначен') ORDER BY o.id;

-- name: bookable_orders
-- Заказы без действующего бронирования.
SELECT o.id, o.destination, o.weight
FROM orders AS o
WHERE o.status = 'создан' AND NOT EXISTS (
    SELECT 1 FROM courier_bookings AS b
    WHERE b.order_id = o.id AND b.is_cancelled = 0
) ORDER BY o.id;

-- name: available_couriers
-- ПР7, 7.2 №25: свободные курьеры на дату с подходящей грузоподъёмностью.
SELECT c.id, c.name, c.capacity
FROM couriers AS c
WHERE c.active = 1 AND c.capacity >= ?
  AND NOT EXISTS (
    SELECT 1 FROM courier_bookings AS b
    WHERE b.courier_id = c.id AND b.delivery_date = ? AND b.is_cancelled = 0
  )
ORDER BY c.capacity, c.name;

-- name: bookings_list
-- ПР7, 7.2 №24: брони вместе с заказом, клиентом и курьером.
SELECT b.id, b.order_id, b.delivery_date, b.is_cancelled,
       o.destination, o.weight, cl.name AS client_name,
       c.name AS courier_name
FROM courier_bookings AS b
JOIN orders AS o ON o.id = b.order_id
JOIN clients AS cl ON cl.id = o.client_id
JOIN couriers AS c ON c.id = b.courier_id
ORDER BY b.delivery_date DESC, b.id DESC;

-- name: booking_for_order
-- Действующее бронирование в карточке заказа.
SELECT b.id, b.delivery_date, c.name AS courier_name
FROM courier_bookings AS b JOIN couriers AS c ON c.id = b.courier_id
WHERE b.order_id = ? AND b.is_cancelled = 0;

-- name: booking_metrics
-- ПР7, 7.2 №26: агрегаты по броням.
SELECT COUNT(*) AS total_bookings,
       COALESCE(SUM(CASE WHEN is_cancelled = 0 THEN 1 ELSE 0 END), 0) AS active_bookings
FROM courier_bookings;

-- name: bookings_by_courier
-- ПР7, 7.2 №26: группировка действующих броней по курьерам.
SELECT c.id, c.name, COUNT(b.id) AS booking_count
FROM couriers AS c
LEFT JOIN courier_bookings AS b
  ON b.courier_id = c.id AND b.is_cancelled = 0
GROUP BY c.id, c.name ORDER BY c.id;
