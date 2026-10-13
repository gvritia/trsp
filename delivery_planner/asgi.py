"""Точка входа Django для сервера, использующего интерфейс ASGI."""

import os

from django.core.asgi import get_asgi_application

# Сообщаем Django, какой модуль настроек загружать при запуске сервера.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'delivery_planner.settings')

# ASGI-сервер импортирует этот объект application и передаёт ему запросы.
application = get_asgi_application()
