"""Консольный интерфейс системы планирования доставки."""

from pathlib import Path

from models import Client, Courier, Order, Route
from models.clients import add_client, find_clients, get_client
from models.couriers import is_courier_available
from models.orders import (
    assign_courier,
    calculate_efficiency,
    cancel_order,
    create_order,
    find_orders,
    sort_orders,
)
from models.routes import complete_route, create_route
from storage import (
    load_clients,
    load_couriers,
    load_orders,
    load_routes,
    save_clients,
    save_couriers,
    save_orders,
    save_routes,
)
from utils import input_float, input_int

DATA_DIR = Path(__file__).parent / "data"
ORDERS_FILE = DATA_DIR / "orders.json"
COURIERS_FILE = DATA_DIR / "couriers.json"
CLIENTS_FILE = DATA_DIR / "clients.json"
ROUTES_FILE = DATA_DIR / "routes.json"


def show_items(items: list[object], empty_message: str) -> None:
    """Полиморфно вывести коллекцию объектов через их методы __str__."""
    if not items:
        print(empty_message)
        return
    for item in items:
        print(item)


def show_couriers(couriers: list[Courier], orders: list[Order]) -> None:
    """Вывести курьеров и рассчитанную методами объектов загрузку."""
    if not couriers:
        print("Список курьеров пуст.")
        return
    for courier in couriers:
        print(f"{courier} | загрузка: {courier.current_load(orders):g} кг")


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
    """Преобразовать номера через запятую в список целых чисел."""
    try:
        order_ids = [int(item.strip()) for item in value.split(",")]
    except ValueError as error:
        raise ValueError(
            "номера заказов должны быть целыми числами"
        ) from error
    if not order_ids or any(order_id < 1 for order_id in order_ids):
        raise ValueError("укажите хотя бы один положительный номер заказа")
    return order_ids


def save_all(
    clients: list[Client],
    couriers: list[Courier],
    orders: list[Order],
    routes: list[Route],
) -> None:
    """Сохранить все коллекции объектов перед завершением программы."""
    save_clients(CLIENTS_FILE, clients)
    save_couriers(COURIERS_FILE, couriers)
    save_orders(ORDERS_FILE, orders)
    save_routes(ROUTES_FILE, routes)


def main() -> None:
    """Загрузить объектный граф и запустить обработку команд пользователя."""
    try:
        clients = load_clients(CLIENTS_FILE)
        couriers = load_couriers(COURIERS_FILE)
        orders = load_orders(ORDERS_FILE, clients, couriers)
        routes = load_routes(ROUTES_FILE, orders, couriers)
    except (KeyError, OSError, TypeError, ValueError) as error:
        print(f"Не удалось запустить приложение: {error}")
        return

    while True:
        print_menu()
        choice = input("Выберите действие: ").strip()
        if choice == "0":
            try:
                save_all(clients, couriers, orders, routes)
                print("Данные сохранены. До свидания!")
            except OSError as error:
                print(f"Не удалось сохранить данные: {error}")
            break

        try:
            if choice == "1":
                show_items(orders, "Список заказов пуст.")
            elif choice == "2":
                destination = input("Адрес доставки: ").strip()
                weight = input_float("Вес заказа, кг: ", minimum=0.01)
                client = get_client(
                    clients, input_int("Номер клиента: ", minimum=1)
                )
                order = create_order(orders, destination, weight, client)
                save_orders(ORDERS_FILE, orders)
                print(f"Заказ #{order.id} создан.")
            elif choice == "3":
                query = input("Адрес, клиент или курьер: ").strip()
                show_items(find_orders(orders, query), "Заказы не найдены.")
            elif choice == "4":
                show_items(sort_orders(orders, key="weight"), "Нет заказов.")
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
                show_items(clients, "Список клиентов пуст.")
            elif choice == "11":
                client = add_client(
                    clients,
                    input("ФИО клиента: ").strip(),
                    input("Телефон клиента: ").strip(),
                )
                save_clients(CLIENTS_FILE, clients)
                print(f"Клиент #{client.id} добавлен.")
            elif choice == "12":
                show_items(routes, "Список маршрутов пуст.")
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
                print(f"Маршрут #{route.id} создан.")
            elif choice == "14":
                route_id = input_int("Номер маршрута: ", minimum=1)
                complete_route(routes, orders, route_id)
                save_routes(ROUTES_FILE, routes)
                save_orders(ORDERS_FILE, orders)
                print(f"Маршрут #{route_id} завершён.")
            elif choice == "15":
                query = input("Имя или телефон клиента: ").strip()
                show_items(find_clients(clients, query), "Клиенты не найдены.")
            else:
                print("Ошибка: выберите существующий пункт меню.")
        except (KeyError, OSError, TypeError, ValueError) as error:
            print(f"Ошибка: {error}")


if __name__ == "__main__":
    main()
