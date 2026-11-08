"""Тесты JSON-преобразования объектной модели."""

from pathlib import Path

import pytest

from models import Client, Courier, Order, Route
from storage import (
    load_clients,
    load_couriers,
    load_orders,
    load_records,
    load_routes,
    save_clients,
    save_couriers,
    save_orders,
    save_routes,
)


def test_object_graph_json_round_trip(tmp_path: Path) -> None:
    client = Client(1, "Анна", "+7-900-111-22-33")
    courier = Courier(1, "Иван", 50.0)
    order = Order(1, "ул. Новая, 1", 12.0, client, "назначен", courier)
    route = Route(1, [order])
    clients_file = tmp_path / "clients.json"
    couriers_file = tmp_path / "couriers.json"
    orders_file = tmp_path / "orders.json"
    routes_file = tmp_path / "routes.json"

    save_clients(clients_file, [client])
    save_couriers(couriers_file, [courier])
    save_orders(orders_file, [order])
    save_routes(routes_file, [route])
    clients = load_clients(clients_file)
    couriers = load_couriers(couriers_file)
    orders = load_orders(orders_file, clients, couriers)
    routes = load_routes(routes_file, orders)

    assert orders[0].client is clients[0]
    assert orders[0].courier is couriers[0]
    assert routes[0].courier is couriers[0]
    assert routes[0].orders[0] is orders[0]
    assert "courier_id" not in load_records(routes_file)[0]


def test_invalid_json_is_reported(tmp_path: Path) -> None:
    file_path = tmp_path / "orders.json"
    file_path.write_text("not json", encoding="utf-8")

    with pytest.raises(ValueError, match="повреждён JSON"):
        load_records(file_path)
