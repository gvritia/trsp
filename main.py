"""Консольный интерфейс системы планирования доставки."""

from pathlib import Path
from typing import Any

from clients import add_client, find_clients, get_client
from couriers import assign_courier, is_courier_available
from orders import (
    calculate_efficiency,
    cancel_order,
    create_order,
    find_orders,
    sort_orders,
)
from routes import complete_route, create_route
from storage import (
    load_clients,
    load_couriers,
    load_orders,
    load_routes,
    save_clients,
    save_orders,
    save_routes,
)
from utils import input_float, input_int

DATA_DIR = Path(__file__).parent / "data"
ORDERS_FILE = DATA_DIR / "orders.json"
COURIERS_FILE = DATA_DIR / "couriers.json"
CLIENTS_FILE = DATA_DIR / "clients.json"
ROUTES_FILE = DATA_DIR / "routes.json"


def show_orders(orders: list[dict[str, Any]]) -> None:
    """Вывести список заказов."""
    if not orders:
        print("Список заказов пуст.")
        return

    print("\n--- Заказы ---")
    for order in orders:
        courier = order.get("courier") or "не назначен"
        client_id = order.get("client_id") or "не указан"
        print(
            f"#{order['id']}: {order['destination']} | "
            f"{order['weight']} кг | {order['status']} | "
            f"клиент: #{client_id} | курьер: {courier}"
        )


def show_couriers(
    couriers: list[dict[str, Any]], orders: list[dict[str, Any]]
) -> None:
    """Вывести курьеров и их текущую загрузку."""
    if not couriers:
        print("Список курьеров пуст.")
        return

    print("\n--- Курьеры ---")
    for courier in couriers:
        assigned_weight = sum(
            float(order["weight"])
            for order in orders
            if order.get("courier") == courier["name"]
            and order.get("status") == "назначен"
        )
        state = "доступен" if courier.get("active", True) else "недоступен"
        print(
            f"{courier['name']}: {assigned_weight:g}/"
            f"{courier['capacity']:g} кг, {state}"
        )


def show_clients(clients: list[dict[str, Any]]) -> None:
    """Вывести список клиентов."""
    if not clients:
        print("Список клиентов пуст.")
        return

    print("\n--- Клиенты ---")
    for client in clients:
        print(f"#{client['id']}: {client['name']} | {client['phone']}")


def show_routes(routes: list[dict[str, Any]]) -> None:
    """Вывести список маршрутов."""
    if not routes:
        print("Список маршрутов пуст.")
        return

    print("\n--- Маршруты ---")
    for route in routes:
        order_numbers = ", ".join(map(str, route["order_ids"]))
        print(
            f"#{route['id']}: курьер {route['courier']} | "
            f"заказы: {order_numbers} | {route['status']}"
        )


def print_menu() -> None:
    """Вывести главное меню приложения."""
    print(
        "\n=== Система планирования маршрутов доставки ===\n"
        "1. Показать заказы\n"
        "2. Создать заказ\n"
        "3. Найти заказ\n"
        "4. Отсортировать заказы по весу\n"
        "5. Показать курьеров\n"
        "6. Проверить доступность курьера\n"
        "7. Назначить курьера\n"
        "8. Отменить заказ\n"
        "9. Показать эффективность\n"
        "10. Показать клиентов\n"
        "11. Добавить клиента\n"
        "12. Показать маршруты\n"
        "13. Создать маршрут\n"
        "14. Завершить маршрут\n"
        "15. Найти клиента\n"
        "0. Выход"
    )


def _parse_order_ids(value: str) -> list[int]:
    """Преобразовать строку номеров через запятую в список целых чисел."""
    try:
        order_ids = [int(item.strip()) for item in value.split(",")]
    except ValueError as error:
        raise ValueError(
            "номера заказов должны быть целыми числами"
        ) from error
    if not order_ids or any(order_id < 1 for order_id in order_ids):
        raise ValueError("укажите хотя бы один положительный номер заказа")
    return order_ids


def main() -> None:
    """Загрузить данные и запустить цикл обработки команд пользователя."""
    try:
        orders = load_orders(ORDERS_FILE)
        couriers = load_couriers(COURIERS_FILE)
        clients = load_clients(CLIENTS_FILE)
        routes = load_routes(ROUTES_FILE)
    except (OSError, ValueError) as error:
        print(f"Не удалось запустить приложение: {error}")
        return

    while True:
        print_menu()
        choice = input("Выберите действие: ").strip()
        if choice == "0":
            print("Данные сохранены. До свидания!")
            break

        try:
            if choice == "1":
                show_orders(orders)
            elif choice == "2":
                destination = input("Адрес доставки: ").strip()
                weight = input_float("Вес заказа, кг: ", minimum=0.01)
                client_id = input_int("Номер клиента: ", minimum=1)
                get_client(clients, client_id)
                order = create_order(
                    orders, destination, weight, client_id=client_id
                )
                save_orders(ORDERS_FILE, orders)
                print(f"Заказ #{order['id']} создан.")
            elif choice == "3":
                query = input("Адрес или имя курьера: ").strip()
                show_orders(find_orders(orders, query))
            elif choice == "4":
                show_orders(sort_orders(orders, key="weight"))
            elif choice == "5":
                show_couriers(couriers, orders)
            elif choice == "6":
                courier_name = input("Имя курьера: ").strip()
                weight = input_float("Вес нового заказа, кг: ", minimum=0)
                available = is_courier_available(
                    couriers, orders, courier_name, weight
                )
                message = "доступен" if available else "недоступен"
                print(f"Курьер {courier_name} {message} для этого заказа.")
            elif choice == "7":
                order_id = input_int("Номер заказа: ", minimum=1)
                courier_name = input("Имя курьера: ").strip()
                assign_courier(orders, couriers, order_id, courier_name)
                save_orders(ORDERS_FILE, orders)
                print(f"Курьер назначен на заказ #{order_id}.")
            elif choice == "8":
                order_id = input_int("Номер заказа: ", minimum=1)
                cancel_order(orders, order_id)
                save_orders(ORDERS_FILE, orders)
                print(f"Заказ #{order_id} отменён.")
            elif choice == "9":
                efficiency = calculate_efficiency(orders)
                print(f"Эффективность назначения: {efficiency:.1f}%")
            elif choice == "10":
                show_clients(clients)
            elif choice == "11":
                name = input("ФИО клиента: ").strip()
                phone = input("Телефон клиента: ").strip()
                client = add_client(clients, name, phone)
                save_clients(CLIENTS_FILE, clients)
                print(f"Клиент #{client['id']} добавлен.")
            elif choice == "12":
                show_routes(routes)
            elif choice == "13":
                courier_name = input("Имя курьера: ").strip()
                raw_ids = input("Номера заказов через запятую: ")
                route = create_route(
                    routes,
                    orders,
                    couriers,
                    courier_name,
                    _parse_order_ids(raw_ids),
                )
                save_routes(ROUTES_FILE, routes)
                print(f"Маршрут #{route['id']} создан.")
            elif choice == "14":
                route_id = input_int("Номер маршрута: ", minimum=1)
                complete_route(routes, orders, route_id)
                save_routes(ROUTES_FILE, routes)
                save_orders(ORDERS_FILE, orders)
                print(f"Маршрут #{route_id} завершён.")
            elif choice == "15":
                query = input("Имя или телефон клиента: ").strip()
                show_clients(find_clients(clients, query))
            else:
                print("Ошибка: выберите существующий пункт меню.")
        except (OSError, ValueError) as error:
            print(f"Ошибка: {error}")


if __name__ == "__main__":
    main()
