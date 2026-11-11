# Подготовка к защите ПР10: вопросы 3 и 4

В проекте системы доставки модель `Booking` хранит бронирование курьера для заказа. Для вопроса 3 подготовлено реальное изменение модели — необязательное примечание и миграция `0005_booking_note`. Для вопроса 4 используются уже существующие миграции перехода от `is_cancelled` к `status`.

## Какие файлы открыть

| Что показать | Полный путь |
| --- | --- |
| Модель и поля `status`, `note` | `C:\Users\user\PycharmProjects\trsp\delivery_bookings\models.py` |
| Новая миграция `AddField` для вопроса 3 | `C:\Users\user\PycharmProjects\trsp\delivery_bookings\migrations\0005_booking_note.py` |
| Старая схема с `is_cancelled` | `C:\Users\user\PycharmProjects\trsp\delivery_bookings\migrations\0001_initial.py` |
| Добавление `status` с начальным `active` | `C:\Users\user\PycharmProjects\trsp\delivery_bookings\migrations\0002_add_status.py` |
| Перенос отменённых записей через `RunPython` | `C:\Users\user\PycharmProjects\trsp\delivery_bookings\migrations\0003_copy_status.py` |
| Удаление старого поля после переноса | `C:\Users\user\PycharmProjects\trsp\delivery_bookings\migrations\0004_alter_booking_options_and_more.py` |
| Проверка миграций на отдельной временной базе | `C:\Users\user\PycharmProjects\trsp\tests\test_pr10.py` |

## Подготовка терминала

Откройте PowerShell в `C:\Users\user\PycharmProjects\trsp`. Все команды ниже запускаются из этой папки. Перед защитой убедитесь, что миграции применены:

```powershell
.\.venv\Scripts\python.exe manage.py showmigrations delivery_bookings
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py check
```

У `0001`–`0005` должны стоять отметки `[X]`, а `makemigrations --check --dry-run` должен вывести `No changes detected`. Если `0005` ещё не применена в вашей копии базы, выполните `.\.venv\Scripts\python.exe manage.py migrate delivery_bookings`.

## Вопрос 3. Изменение модели и миграция

1. В `delivery_bookings/models.py` покажите поле `note = models.CharField(...)` у `Booking`. Объясните параметры: `max_length=255` ограничивает длину строки; `blank=True` разрешает оставить поле пустым в формах; `default=""` даёт прежним записям пустую строку. `null` не требуется, поэтому в базе для отсутствующего примечания хранится `""`, а не `NULL`.
2. Откройте `0005_booking_note.py`. Покажите `dependencies` (миграция идёт после `0004`) и `operations` с `migrations.AddField(...)`. Это изменение схемы базы: у таблицы бронирований появляется столбец `note`. Файл создан командой `makemigrations`; её результат при подготовке был `+ Add field note to booking`.
3. В терминале выполните `showmigrations delivery_bookings` и покажите `[X] 0005_booking_note`: команда `migrate delivery_bookings` уже применила изменение. Затем проверьте существующие записи:

   ```powershell
   .\.venv\Scripts\python.exe manage.py shell -c "from delivery_bookings.models import Booking; print(list(Booking.objects.values('id', 'status', 'note')))"
   ```

   У существующего бронирования останутся прежние `id` и `status`, а `note` будет пустой строкой. В текущей локальной базе после миграции проверена запись `{'id': 1, 'status': 'active', 'note': ''}`. Если состав вашей базы изменится, ориентируйтесь на фактический вывод.
4. **Если преподаватель просит создать новую миграцию прямо при нём:** временно увеличьте в модели `max_length=255` до `max_length=300` у поля `note`, сохраните файл и выполните:

   ```powershell
   .\.venv\Scripts\python.exe manage.py makemigrations delivery_bookings
   .\.venv\Scripts\python.exe manage.py migrate delivery_bookings
   .\.venv\Scripts\python.exe manage.py showmigrations delivery_bookings
   ```

   Откройте новый файл `delivery_bookings/migrations/0006_alter_booking_note.py` (точное имя покажет `makemigrations`). В нём будет `migrations.AlterField`, потому что изменился параметр существующего поля. Покажите `[X]` у новой миграции и снова выполните запрос из шага 3: данные бронирования сохраняются. После применения оставьте в модели `max_length=300` и сохраните новый файл миграции вместе с кодом: удалять применённую миграцию нельзя.

**Короткий ответ преподавателю:** «Я добавил необязательное поле `note` в модель `Booking`. `makemigrations` создала `AddField` с зависимостью от предыдущей миграции, а `migrate` добавила столбец в базу. Существующие записи остались на месте и получили значение `""` из `default`. При изменении `max_length` новая миграция содержит `AlterField`».

## Вопрос 4. Преобразование существующих данных

1. Откройте `0001_initial.py` и покажите прежний `BooleanField is_cancelled`: `False` означал действующее бронирование, `True` — отменённое.
2. В `0002_add_status.py` покажите новое поле `status` со значением по умолчанию `active`. После этой миграции все старые строки временно имеют `status='active'`, включая отменённые. Поэтому сразу удалять `is_cancelled` нельзя.
3. В `0003_copy_status.py` покажите `migrations.RunPython(copy_status, migrations.RunPython.noop)`. Внутри `copy_status()` берётся **историческая модель** через `apps.get_model(...)`, выбираются строки с `is_cancelled=True`, и их `status` меняется на `cancelled`. Строки с `False` остаются `active`.
4. В `0004_alter_booking_options_and_more.py` покажите `migrations.RemoveField(..., name='is_cancelled')`. Старый столбец удаляется только после переноса значений. Ограничения уникальности теперь проверяют `status='active'`.
5. Для фактической проверки откройте в `tests/test_pr10.py` функцию `test_booking_statuses_survive_data_and_schema_migrations` и запустите:

   ```powershell
   .\.venv\Scripts\python.exe -m pytest -v tests/test_pr10.py::test_booking_statuses_survive_data_and_schema_migrations
   ```

   Тест создаёт **отдельную временную базу**, применяет старую миграцию `0001`, добавляет две старые записи (`is_cancelled=1` и `0`), затем применяет `0002`–`0004`. Покажите в коде проверку результата: первая запись стала `cancelled`, вторая — `active`, столбец `is_cancelled` удалён. После этого тест присваивает второй записи новый статус `completed`, применяет `0005` и подтверждает, что статусы `cancelled` и `completed` сохранились, а поле `note` заполнено пустой строкой.

**Короткий ответ преподавателю:** «Миграция схемы добавляет или удаляет столбцы; миграция данных переводит содержимое существующих строк. Сначала мы добавили `status`, затем `RunPython` преобразовала старые `is_cancelled=True` в `cancelled`, и только после этого удалили `is_cancelled`. Старое булево поле не могло отличить завершённую бронь от действующей: `completed` — новое состояние, которое появляется после перехода и сохраняется последующими миграциями».

## Проверка перед защитой

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe -m pytest -q tests/test_pr10.py::test_booking_statuses_survive_data_and_schema_migrations
.\.venv\Scripts\python.exe -m flake8 .
```

Если на защите выполнен шаг с `max_length=300`, `makemigrations --check --dry-run` запускайте **после** создания `0006`: только тогда модель и история миграций снова совпадут.

Полный набор тестов проекта рассчитан на исходные данные без бронирований. Если вы уже создали бронь для демонстрации, запускайте весь набор на отдельной временной базе, чтобы не удалять ваши записи. При подготовке таким способом прошли все 42 теста.
