# ПР10: проверка проекта по разделу с 166-й страницы

Учебный пример использует `Room`, `User` и `Booking`. В системе доставки бронируемый ресурс — `Courier`, заказчик — `Client`, бронь — `Booking`; дополнительно сохранены `Order` и `Route`.

## Подготовка

```powershell
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py import_legacy_data  # только если ORM-таблицы ещё пусты
python manage.py createsuperuser
python manage.py runserver
```

Зайдите на `/admin/` под созданной учётной записью. Суперпользователь и пароль не хранятся в репозитории.

## Что показать

| Требование | Место проверки |
| --- | --- |
| Django Admin: модели, русские названия, поиск, фильтры, сортировка, inline | `/admin/`; `*/admin.py`, `*/apps.py`, `*/models.py` |
| Сохранение прежних бронирований при переходе на TextChoices | миграции `delivery_bookings/0002`–`0004`; `test_cancelled_bookings_survive_status_migration` |
| Менеджер и методы QuerySet | `delivery_bookings/models.py`: `active()`, `cancelled()`, `completed()`, `for_date()` |
| Фильтрация, сортировка и пагинация вместе | `/bookings/?status=active&sort=date`; `delivery_bookings/views.py` |
| Свободные курьеры по дате и статусу | `/bookings/available/`; `delivery_bookings/services.py` |
| Статистика по трём статусам | `/statistics/`; `homepage/views.py` |
| Детали по slug и «Посмотреть на сайте» | `/routes/by-slug/marshrut-1/`; `Route.get_absolute_url()` |
| Общий контекст навигации | `homepage/context_processors.py`; число курьеров в меню |
| SQL-анализ | Django Debug Toolbar на `/bookings/` и `/bookings/<id>/` при `DJANGO_DEBUG=1` |
| Сохранение старых страниц | `/routes/1/`, `/orders/1/`, главная, списки и статистика |

`GeneratedField` в предметную модель не добавлялось: нет производного значения, которое нужно хранить в самой базе. Вместо этого для демонстрации изменений модели используются миграции статуса бронирования и slug маршрута. Прежняя SQLite и JSON остаются материалом предыдущей работы; прямые SQL-запросы не используются в новых представлениях.

## Проверка запросов

На странице списка бронирований Debug Toolbar показывает запрос подсчёта для пагинации, запрос текущей страницы и запросы для вариантов выбора в фильтрах. Детальная страница загружает заказ, клиента и курьера через `select_related()`. Тест `test_booking_filters_pagination_and_related_query` дополнительно проверяет, что после загрузки бронирования обращение к этим связям не вызывает новых запросов: вся цепочка получается за один запрос; при отображении страницы добавляется запрос контекстного процессора. Изменение статуса на `COMPLETED` через админку освобождает курьера на дату бронирования.

```powershell
python manage.py makemigrations --check --dry-run
python manage.py showmigrations
python manage.py check
python -m pytest -v
python -m flake8 .
git status
```

Для отчёта делайте скриншоты работающего приложения и терминала: список моделей в админке, поиск и фильтр бронирований, inline у курьера или заказа, список бронирований с пагинацией, статистику, SQL-панель Debug Toolbar и результаты команд проверки. При проверке доступности используйте одну дату до и после изменения статуса бронирования.
