"""Проверка страниц ПР5 на реальных данных проекта."""

import os

import django
from django.conf import settings
from django.test import Client, override_settings

from storage import load_delivery_data


def setup_module() -> None:
    """Инициализировать Django без дополнительного pytest-плагина."""
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "delivery_planner.settings"
    )
    django.setup()


def test_web_pages_show_existing_data() -> None:
    """Все основные страницы показывают актуальные объекты из JSON."""
    _, _, orders, routes = load_delivery_data(settings.BASE_DIR / "data")
    assert orders and routes
    order = orders[0]
    route = routes[0]
    client = Client(HTTP_HOST="localhost")

    for url in ("/", "/orders/", "/routes/"):
        assert client.get(url).status_code == 200

    order_response = client.get(f"/orders/{order.id}/")
    assert order_response.status_code == 200
    assert order.destination in order_response.content.decode("utf-8")
    assert order.client.name in order_response.content.decode("utf-8")

    route_response = client.get(f"/routes/{route.id}/")
    assert route_response.status_code == 200
    assert route.courier.name in route_response.content.decode("utf-8")
    assert f"Заказ #{route.orders[0].id}" in route_response.content.decode(
        "utf-8"
    )


@override_settings(DEBUG=False)
def test_missing_objects_and_unknown_url_return_404() -> None:
    """Отсутствующие ID и URL возвращают оформленную страницу 404."""
    _, _, orders, routes = load_delivery_data(settings.BASE_DIR / "data")
    missing_order_id = max(order.id for order in orders) + 1
    missing_route_id = max(route.id for route in routes) + 1
    client = Client(HTTP_HOST="localhost")

    for url in (
        f"/orders/{missing_order_id}/",
        f"/routes/{missing_route_id}/",
        "/unknown-page/",
    ):
        response = client.get(url)
        assert response.status_code == 404
        assert "<!DOCTYPE html>" in response.content.decode("utf-8")
