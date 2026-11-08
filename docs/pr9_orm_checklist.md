# ПР9: демонстрация Django ORM

Проект использует сущности доставки вместо учебных `Room`, `User`, `Booking`: `Order`, `Client`/`Courier`, `Booking`. Существующие страницы и сценарии доставки сохранены.

## Что показать в проекте

| Требование | Где показать |
| --- | --- |
| Модели, типы полей, первичные и внешние ключи | `homepage/models.py`, `delivery_orders/models.py`, `delivery_routes/models.py`, `delivery_bookings/models.py` |
| Связи и обратный доступ | `client.orders`, `courier.orders`, `order.bookings`, `route.orders` |
| Миграции | `*/migrations/0001_initial.py`; команды ниже |
| Перенос предыдущих данных | `homepage/management/commands/import_legacy_data.py`; прежняя SQLite и JSON остаются на месте |
| Создание, изменение и удаление через ORM | `Booking.objects.create()`, `booking.cancel()`; операции с временными объектами в `tests/test_orm.py` |
| Поиск, фильтрация, сортировка, пагинация | `/orders/`, `/bookings/available/`, `delivery_orders/views.py` |
| Агрегация, `values()`, `annotate()` | `/statistics/`, `homepage/views.py` |
| Данные в шаблонах | контекст представлений и шаблоны четырёх приложений |
| Отменённые брони не блокируют доступность | `delivery_bookings/services.py`, `tests/test_orm.py` |
| Неизвестные ID, пустые результаты, ошибка ввода | `tests/test_web.py` |

```powershell
python manage.py makemigrations --check --dry-run
python manage.py showmigrations homepage delivery_orders delivery_routes delivery_bookings
python manage.py check
python -m pytest -q
```

## Пятнадцать ORM-выражений для Django shell

Запустить `python manage.py shell`, затем ввести импорты:

```python
from django.db.models import Avg, Count, Q, Sum
from homepage.models import Client, Courier
from delivery_orders.models import Order
from delivery_routes.models import Route
from delivery_bookings.models import Booking
```

Далее каждое выражение можно выполнить отдельно. Все они только читают базу.

```python
Client.objects.all()                                      # 1. Все клиенты
Order.objects.filter(status="создан")                    # 2. Один фильтр
Order.objects.filter(status="создан", weight__gte=50)    # 3. Два фильтра
Order.objects.exclude(status="отменён")                  # 4. Исключение
Order.objects.filter(destination__icontains="Мира")     # 5. Поиск
Order.objects.order_by("-weight")                         # 6. Сортировка
Order.objects.order_by("id")[0:2]                        # 7. Страница
Order.objects.values("id", "status")                     # 8. Отдельные поля
Order.objects.select_related("client", "courier")        # 9. Прямые связи
Client.objects.get(pk=1).orders.all()                     # 10. Обратная связь
Route.objects.get(pk=1).orders.all()                      # 11. Многие ко многим
Order.objects.filter(Q(status="создан") | Q(weight__gt=60))  # 12. OR
Order.objects.aggregate(average_weight=Avg("weight"))   # 13. Агрегат
Order.objects.values("status").annotate(count=Count("id"), weight=Sum("weight"))  # 14. Группировка
Courier.objects.annotate(bookings_count=Count("bookings", filter=Q(bookings__status=Booking.Status.ACTIVE)))  # 15. Условный счётчик
```

Для проверки связи бронирования в shell при наличии записей: `booking = Booking.objects.select_related("order", "courier").first()`, затем `booking.order`, `booking.courier`, `booking.order.client`. Если бронирований пока нет, создайте одно через страницу `/bookings/available/` и повторите проверку. Отмена брони остаётся видна в `/bookings/`, но курьер вновь появляется в поиске свободных на эту дату.
