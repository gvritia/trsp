# Форматирование и проверка кода в PyCharm

В VS Code форматирование и проверка Python обычно подключаются расширениями.
В PyCharm основные возможности уже встроены, поэтому отдельное расширение для
обычного форматирования не обязательно.

## Встроенное форматирование PyCharm

1. Откройте корневой каталог проекта в окне Project.
2. Выберите нужный файл или весь проект.
3. Выполните **Code → Reformat Code**.
4. Горячая клавиша в Windows: `Ctrl+Alt+L`.
5. Для удаления неиспользуемых импортов выполните **Code → Optimize Imports**
   или нажмите `Ctrl+Alt+O`.

Стиль Python настраивается в **Settings → Editor → Code Style → Python**. Для
этой работы используется ограничение строки в 79 символов по PEP 8. Файл
`.editorconfig` автоматически передаёт PyCharm отступ в четыре пробела и
ограничение длины строки.

## Форматтер Black

Black добавлен в `requirements.txt`, а его параметры хранятся в
`pyproject.toml`. После установки зависимостей весь проект форматируется
командой из встроенного терминала PyCharm:

```powershell
python -m black .
```

В новых версиях PyCharm Black можно включить в разделе
**Settings → Tools → Black** и активировать запуск при сохранении файла. Если
этого пункта в используемой версии нет, достаточно запускать команду выше.

## Проверка flake8 в PyCharm

Проверка, которую требует методическое указание, выполняется в терминале из
корня проекта:

```powershell
python -m flake8
```

Для запуска через меню PyCharm добавьте External Tool:

1. Откройте **Settings → Tools → External Tools**.
2. Нажмите `+` и укажите имя `flake8`.
3. Program: `$PyInterpreterDirectory$\python.exe`.
4. Arguments: `-m flake8`.
5. Working directory: `$ProjectFileDir$`.

После этого проверка доступна через **Tools → External Tools → flake8**.

## Рекомендуемый порядок проверки

```powershell
python -m black .
python -m flake8
python -m pytest
```

Команды запускаются из каталога `C:\Users\user\PycharmProjects\trsp`, а не из
каталога `tests`.
