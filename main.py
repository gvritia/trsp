"""Консольный интерфейс системы планирования доставки."""

from pathlib import Path
from typing import Any

from couriers import assign_courier, is_courier_available
from orders import (
    calculate_efficiency,
    cancel_order,
    create_order,
    find_orders,
    sort_orders,
)
from storage import load_couriers, load_orders, save_orders
from utils import input_float, input_int


DATA_DIR = Path(__file__).parent / "data"
ORDERS_FILE = DATA_DIR / "orders.json"
COURIERS_FILE = DATA_DIR / "couriers.json"


def show_orders(orders: list[dict[str, Any]]) -> None:
    """Вывести список заказов."""
    if not orders:
        print("Список заказов пуст.")
        return

    print("\n--- Заказы ---")
    for order in orders:
        courier = order.get("courier") or "не назначен"
        print(
            f"#{order['id']}: {order['destination']} | "
            f"{order['weight']} кг | {order['status']} | "
            f"курьер: {courier}"
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
        "0. Выход"
    )


def main() -> None:
    """Загрузить данные и запустить цикл обработки команд пользователя."""
    orders = load_orders(ORDERS_FILE)
    couriers = load_couriers(COURIERS_FILE)

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
                order = create_order(orders, destination, weight)
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
            else:
                print("Ошибка: выберите пункт меню от 0 до 9.")
        except (OSError, ValueError) as error:
            print(f"Ошибка: {error}")


if __name__ == "__main__":
    main()
