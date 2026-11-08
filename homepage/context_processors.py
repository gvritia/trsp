"""Общие значения для навигации всех страниц проекта."""

from .models import Courier


def site_navigation(request):
    return {
        "site_title": "Система доставки",
        "site_courier_count": Courier.objects.count(),
    }
