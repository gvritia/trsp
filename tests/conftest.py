"""Инициализация Django до импорта ORM-моделей в тестах."""

import os

import django
import pytest
from django.db import transaction

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "delivery_planner.settings")
django.setup()


@pytest.fixture
def rollback_orm():
    """Откатить ORM-записи, сделанные веб-тестом в локальной базе."""
    with transaction.atomic():
        yield
        transaction.set_rollback(True)
