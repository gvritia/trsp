"""Точка входа Django для обычного синхронного WSGI-сервера."""

import os

from django.core.wsgi import get_wsgi_application

# Этот модуль настроек будет использован, если переменная ещё не задана.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'delivery_planner.settings')

# WSGI-сервер импортирует этот объект application для обработки HTTP-запросов.
application = get_wsgi_application()
