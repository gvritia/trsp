"""ПР7, 7.2 №23–24, №26, №29: страницы на данных SQLite."""

import os

import django
from django.contrib.staticfiles import finders
from django.conf import settings
from django.test import Client, override_settings
from django.urls import reverse

from django.template.loader import render_to_string
from delivery_bookings.models import Booking
from delivery_routes.models import Route
from storage import load_delivery_data


def setup_module() -> None:
    """Инициализировать Django без дополнительного pytest-плагина."""
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "delivery_planner.settings"
    )
    django.setup()


def test_web_pages_show_existing_data() -> None:
    """Основные страницы показывают связанные данные из SQLite."""
    _, _, orders, routes = load_delivery_data(settings.BASE_DIR / "data")
    assert orders and routes
    order = orders[0]
    route = routes[0]
    client = Client(HTTP_HOST="localhost")

    for url in (
        "/",
        "/orders/",
        "/routes/",
        "/statistics/",
        "/bookings/",
        "/bookings/available/",
    ):
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
    route_slug_url = Route.objects.get(pk=route.id).get_absolute_url()
    assert route_slug_url in route_list_html
    assert client.get(route_slug_url).status_code == 200

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


def test_empty_lists_use_template_fallback() -> None:
    """Пустые коллекции отображаются через тег empty в шаблонах."""
    assert "Заказов не найдено" in render_to_string(
        "delivery_orders/order_list.html",
        {"orders": [], "statuses": {}, "total_orders": 0},
    )
    assert "Маршрутов пока нет" in render_to_string(
        "delivery_routes/route_list.html", {"routes": []}
    )


def test_search_filter_and_statistics() -> None:
    """Проверить параметризованный поиск, фильтр и агрегаты на страницах."""
    client = Client(HTTP_HOST="localhost")
    search = client.get("/orders/", {"q": "Мира"}).content.decode("utf-8")
    assert "пр. Мира, 10" in search
    assert "ул. Ленина, 15" not in search

    literal = client.get("/orders/", {"q": "%"}).content.decode("utf-8")
    assert "Заказов не найдено" in literal

    filtered = client.get("/orders/", {"status": "создан"}).content.decode(
        "utf-8"
    )
    assert "Кремль, 1" in filtered
    assert "ул. Ленина, 15" not in filtered

    combined = client.get(
        "/orders/", {"q": "Мира", "status": "создан"}
    ).content.decode("utf-8")
    assert "Заказов не найдено" in combined

    statistics = client.get("/statistics/").content.decode("utf-8")
    assert "Статистика доставки" in statistics
    assert "Курьеры с назначенными заказами" in statistics
    assert "Алексей" in statistics
    assert "Анна Смирнова" in statistics


def test_booking_pages_search_reserve_and_cancel(rollback_orm) -> None:
    """Полный путь через ORM с откатом изменений после теста."""
    client = Client(HTTP_HOST="localhost")
    day = "2026-10-20"

    available = client.get(
        "/bookings/available/", {"date": day, "order_id": "3"}
    )
    html = available.content.decode("utf-8")
    assert available.status_code == 200
    assert "Алексей" in html
    assert "Иван" not in html
    assert "Забронировать" in html

    csrf_client = Client(HTTP_HOST="localhost", enforce_csrf_checks=True)
    assert (
        csrf_client.post(
            "/bookings/create/", {"date": day, "order_id": 3, "courier_id": 3}
        ).status_code
        == 403
    )
    created = client.post(
        "/bookings/create/", {"date": day, "order_id": 3, "courier_id": 3}
    )
    assert created.status_code == 302
    assert "Алексей" in client.get("/orders/3/").content.decode("utf-8")
    assert day in client.get("/bookings/").content.decode("utf-8")
    stats = client.get("/statistics/").content.decode("utf-8")
    assert "действующих: 1" in stats
    assert "На эту дату подходящих" in client.get(
        "/bookings/available/", {"date": day, "order_id": "4"}
    ).content.decode("utf-8")

    booking_id = Booking.objects.active().get(order_id=3).id
    assert client.post(f"/bookings/{booking_id}/cancel/").status_code == 302
    assert "Отменено" in client.get("/bookings/").content.decode("utf-8")
    stats = client.get("/statistics/").content.decode("utf-8")
    assert "действующих: 0" in stats


def test_order_pages_offer_active_filter_and_pagination() -> None:
    client = Client(HTTP_HOST="localhost")
    first = client.get("/orders/").content.decode("utf-8")
    second = client.get("/orders/", {"page": "2"}).content.decode("utf-8")
    assert "Следующая" in first
    assert "Кремль, 1" not in first
    assert "Кремль, 1" in second
    active = client.get("/orders/", {"status": "активные"}).content.decode(
        "utf-8"
    )
    assert "Кремль, 1" in active
    assert "ул. Ленина, 15" in active
