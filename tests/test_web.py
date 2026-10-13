"""Проверка страниц ПР5 на реальных данных проекта."""

import os

import django
from django.contrib.staticfiles import finders
from django.conf import settings
from django.test import Client, override_settings
from django.urls import reverse

from delivery_orders import views as order_views
from delivery_routes import views as route_views
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
        response = client.get(url)
        assert response.status_code == 200
        assert b"/static/homepage/css/style.css" in response.content
        assert b"/static/homepage/js/main.js" in response.content
        assert b"/static/homepage/img/delivery-logo.svg" in response.content

    order_list_html = client.get("/orders/").content.decode("utf-8")
    assert order.destination in order_list_html
    assert reverse("delivery_orders:detail", args=[order.id]) in (
        order_list_html
    )
    route_list_html = client.get("/routes/").content.decode("utf-8")
    assert route.courier.name in route_list_html
    assert reverse("delivery_routes:detail", args=[route.id]) in (
        route_list_html
    )

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


@override_settings(DEBUG=True)
def test_route_id_errors_have_distinct_messages() -> None:
    """Отличать неизвестный номер маршрута от нечислового ID."""
    _, _, _, routes = load_delivery_data(settings.BASE_DIR / "data")
    missing_route_id = max(155555, max(route.id for route in routes) + 1)
    client = Client(HTTP_HOST="localhost")

    missing = client.get(f"/routes/{missing_route_id}/")
    invalid = client.get("/routes/jhjhhh/")

    assert missing.status_code == invalid.status_code == 404
    missing_html = missing.content.decode("utf-8")
    invalid_html = invalid.content.decode("utf-8")
    assert "Маршрут не найден" in missing_html
    assert f"Маршрут с ID {missing_route_id} не найден" in missing_html
    assert "Некорректный ID маршрута" in invalid_html
    assert "ID маршрута должен быть" in invalid_html
    assert missing_html != invalid_html


def test_project_static_files_are_discoverable() -> None:
    """Проверить CSS, JavaScript и изображение в Django staticfiles."""
    for asset in (
        "homepage/css/style.css",
        "homepage/js/main.js",
        "homepage/img/delivery-logo.svg",
    ):
        assert finders.find(asset) is not None


def test_empty_lists_use_template_fallback(monkeypatch) -> None:
    """Пустые коллекции отображаются через тег empty в шаблонах."""
    def empty_data(data_dir):
        return [], [], [], []

    monkeypatch.setattr(order_views, "load_delivery_data", empty_data)
    monkeypatch.setattr(route_views, "load_delivery_data", empty_data)
    client = Client(HTTP_HOST="localhost")

    assert "Заказов пока нет" in client.get("/orders/").content.decode(
        "utf-8"
    )
    assert "Маршрутов пока нет" in client.get("/routes/").content.decode(
        "utf-8"
    )
