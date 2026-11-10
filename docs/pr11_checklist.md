# ПР11: Django Forms в системе доставки

## Реализация

| Пункт | Где проверить |
| --- | --- |
| GET-фильтрация через `forms.Form`, `is_valid()` и `cleaned_data` | `delivery_bookings/forms.py`, `views.py`, `/bookings/` |
| Сортировка и пагинация вместе с фильтрами | `/bookings/?status=active&sort=date`; ссылки страниц сохраняют параметры |
| Создание через `forms.ModelForm` | `/bookings/create/`; GET показывает форму, POST сохраняет бронь |
| Валидация даты, заказа и курьера | `BookingForm.clean_delivery_date()` и `clean()` |
| Ошибки рядом с полями, сохранение введённых значений | `booking_form.html` |
| Редактирование существующей записи | `/bookings/<id>/edit/`, `ModelForm(instance=booking)` |
| Исключение текущей записи из проверки конфликта | `.exclude(pk=self.instance.pk)` в `BookingForm.clean()` |
| Обработка отсутствующей записи | `get_object_or_404()` в представлении редактирования |
| Отмена без удаления, POST и CSRF | `/bookings/<id>/cancel/`, `Booking.cancel()` |
| Работа прежних сценариев | `/bookings/available/`, маршруты, заказы, Django Admin |

Новые пользовательские формы не требуют миграций моделей. Ранее созданные миграции и данные остаются на месте.

## Проверки

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations
python -m pytest -v
python -m flake8 .
```

Тесты `tests/test_pr11.py` проверяют создание, прошедшую дату, отсутствие обязательных значений, несуществующий заказ, конфликт по курьеру, редактирование без ложного конфликта с самим собой, сохранение ID, ошибочные фильтры, отмену и защиту POST/CSRF. `tests/test_web.py` сохраняет проверку предыдущего пользовательского пути. Для отчёта снимайте изображения работающего приложения и результатов команд: текстовые заглушки из задания не заменяют фактические скриншоты.
