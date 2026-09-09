orders = []  # Список заказов
couriers = ["Иван", "Мария", "Алексей"]  # Доступные курьеры


# ============== Функция 1: Создание заказа ==============

def create_order(destination, weight):
    """Создает новый заказ"""
    if weight <= 0:
        print("Ошибка: вес должен быть больше 0")
        return None

    order = {
        "id": len(orders) + 1,
        "destination": destination,
        "weight": weight,
        "status": "создан",
        "courier": None
    }
    orders.append(order)
    print(f"Заказ #{order['id']} создан: {destination}, {weight} кг")
    return order


# ============== Функция 2: Назначение курьера ==============

def assign_courier(order, courier_name):
    """Назначает курьера на заказ"""
    if order is None:
        print("Ошибка: заказ не найден")
        return False

    if courier_name not in couriers:
        print(f"Ошибка: курьер {courier_name} не найден")
        return False

    if order["status"] != "создан":
        print(f"Ошибка: заказ уже {order['status']}")
        return False

    # Проверка грузоподъемности (упрощенно)
    if order["weight"] > 50:
        print(f"Предупреждение: вес {order['weight']} кг превышает норму")

    order["courier"] = courier_name
    order["status"] = "назначен"
    print(f"Курьер {courier_name} назначен на заказ #{order['id']}")
    return True


# ============== Функция 3: Расчет эффективности ==============

def calculate_efficiency():
    """Рассчитывает процент назначенных заказов"""
    if len(orders) == 0:
        print("Нет заказов")
        return 0.0

    assigned = 0
    for order in orders:
        if order["status"] == "назначен":
            assigned += 1

    efficiency = (assigned / len(orders)) * 100

    print(f"\n--- Статистика ---")
    print(f"Всего заказов: {len(orders)}")
    print(f"Назначено: {assigned}")
    print(f"Эффективность: {round(efficiency, 1)}%")

    if efficiency >= 70:
        print("Оценка: хорошо")
    elif efficiency >= 40:
        print("Оценка: удовлетворительно")
    else:
        print("Оценка: требуется улучшение")

    return efficiency


# ============== Основной сценарий ==============

def main():
    print("=== Система доставки ===\n")

    # Создание заказов
    order1 = create_order("ул. Ленина, 15", 25.5)
    order2 = create_order("пр. Мира, 10", 10.0)
    order3 = create_order("ул. Тверская, 5", -5.0)  # Ошибка
    order4 = create_order("Кремль, 1", 60.0)

    # Назначение курьеров
    assign_courier(order1, "Иван")
    assign_courier(order2, "Мария")
    assign_courier(order3, "Алексей")  # order3 = None
    assign_courier(order4, "Петр")  # Курьер не найден
    assign_courier(order1, "Алексей")  # Уже назначен

    # Расчет эффективности
    calculate_efficiency()

    # Вывод всех заказов
    print("\n--- Все заказы ---")
    for o in orders:
        print(
            f"#{o['id']}: {o['destination']} | {o['weight']} кг | {o['status']} | Курьер: {o['courier'] or 'не назначен'}")


if __name__ == "__main__":
    main()