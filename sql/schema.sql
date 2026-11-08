-- ПР7, 7.6 №1: это описание структуры базы, а не сама база.
-- db/import_json.py выполняет этот файл в SQLite data/delivery.sqlite.
-- SQL-запросы на чтение данных находятся отдельно в sql/queries.sql.
-- ПР7, 7.6 №2–3: ниже шесть таблиц предметной области и их связи.

-- №2: клиенты — имя и телефон получателя заказа.
-- INTEGER PRIMARY KEY задаёт уникальный номер записи; NOT NULL запрещает пустое поле.
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT NOT NULL
);

-- №2: курьеры — имя, грузоподъёмность в кг и признак активности (0 или 1).
-- CHECK не даст записать нулевую грузоподъёмность или иное значение active.
CREATE TABLE IF NOT EXISTS couriers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    capacity REAL NOT NULL CHECK (capacity > 0),
    active INTEGER NOT NULL CHECK (active IN (0, 1))
);

-- №2–3: заказ принадлежит одному существующему клиенту (client_id).
-- courier_id может быть NULL: у только что созданного заказа курьер ещё не назначен.
-- REFERENCES — внешний ключ; он ссылается на первичный ключ другой таблицы.
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    destination TEXT NOT NULL,
    weight REAL NOT NULL CHECK (weight > 0),
    client_id INTEGER NOT NULL REFERENCES clients(id),
    courier_id INTEGER REFERENCES couriers(id),
    status TEXT NOT NULL CHECK (status IN ('создан', 'назначен', 'отменён', 'доставлен')),
    CHECK (status <> 'назначен' OR courier_id IS NOT NULL)
);

-- №2–3: маршрут содержит заказы, а курьер определяется через orders.courier_id.
-- Отдельный courier_id здесь не нужен: он дублировал бы назначение заказа.
CREATE TABLE IF NOT EXISTS routes (
    id INTEGER PRIMARY KEY,
    status TEXT NOT NULL CHECK (status IN ('запланирован', 'завершён'))
);

-- №2–3: таблица связи позволяет включить в маршрут несколько заказов.
-- Пара (route_id, order_id) — составной PK; UNIQUE(order_id) не даёт одному
-- заказу одновременно принадлежать нескольким маршрутам.
-- ON DELETE CASCADE удаляет связи при удалении маршрута, но не сами заказы.
CREATE TABLE IF NOT EXISTS route_orders (
    route_id INTEGER NOT NULL REFERENCES routes(id) ON DELETE CASCADE,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    PRIMARY KEY (route_id, order_id),
    UNIQUE (order_id)
);

-- Все заказы одного маршрута должны быть назначены одному курьеру.
-- При изменении назначения уже включённого заказа связь тоже проверяется.
CREATE TRIGGER IF NOT EXISTS route_order_same_courier_insert
BEFORE INSERT ON route_orders
BEGIN
    SELECT RAISE(ABORT, 'routed order must have a courier')
    WHERE (SELECT courier_id FROM orders WHERE id = NEW.order_id) IS NULL;
    SELECT RAISE(ABORT, 'route orders must have the same courier')
    WHERE EXISTS (
        SELECT 1 FROM route_orders AS ro
        JOIN orders AS existing ON existing.id = ro.order_id
        WHERE ro.route_id = NEW.route_id
          AND existing.courier_id <> (
              SELECT courier_id FROM orders WHERE id = NEW.order_id
          )
    );
END;

CREATE TRIGGER IF NOT EXISTS route_order_same_courier_update
BEFORE UPDATE OF route_id, order_id ON route_orders
BEGIN
    SELECT RAISE(ABORT, 'routed order must have a courier')
    WHERE (SELECT courier_id FROM orders WHERE id = NEW.order_id) IS NULL;
    SELECT RAISE(ABORT, 'route orders must have the same courier')
    WHERE EXISTS (
        SELECT 1 FROM route_orders AS ro
        JOIN orders AS existing ON existing.id = ro.order_id
        WHERE ro.route_id = NEW.route_id
          AND NOT (ro.route_id = OLD.route_id AND ro.order_id = OLD.order_id)
          AND existing.courier_id <> (
              SELECT courier_id FROM orders WHERE id = NEW.order_id
          )
    );
END;

CREATE TRIGGER IF NOT EXISTS routed_order_courier_immutable
BEFORE UPDATE OF courier_id ON orders
WHEN OLD.courier_id IS NOT NEW.courier_id
  AND EXISTS (SELECT 1 FROM route_orders WHERE order_id = OLD.id)
BEGIN
    SELECT RAISE(ABORT, 'remove order from route before changing courier');
END;

-- №2–3: бронь связывает существующие заказ и курьера с датой доставки.
-- is_cancelled = 1 оставляет отменённую бронь в истории. Статус заказа не меняется.
-- Проверка GLOB задаёт форму даты; Python дополнительно проверяет календарную дату.
CREATE TABLE IF NOT EXISTS courier_bookings (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    courier_id INTEGER NOT NULL REFERENCES couriers(id),
    delivery_date TEXT NOT NULL,
    is_cancelled INTEGER NOT NULL DEFAULT 0 CHECK (is_cancelled IN (0, 1)),
    CHECK (delivery_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]')
);

-- Два частичных уникальных индекса запрещают двойную действующую бронь:
-- один курьер на одну дату и один заказ одновременно.
CREATE UNIQUE INDEX IF NOT EXISTS uq_booking_courier_date
ON courier_bookings(courier_id, delivery_date) WHERE is_cancelled = 0;
CREATE UNIQUE INDEX IF NOT EXISTS uq_booking_order
ON courier_bookings(order_id) WHERE is_cancelled = 0;

CREATE INDEX IF NOT EXISTS idx_orders_client ON orders(client_id);
CREATE INDEX IF NOT EXISTS idx_orders_courier ON orders(courier_id);
CREATE INDEX IF NOT EXISTS idx_bookings_date ON courier_bookings(delivery_date);
