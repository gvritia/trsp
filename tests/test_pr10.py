"""Сценарии административной панели и ORM из ПР10."""

import os
import sqlite3
import subprocess
import sys
from datetime import date, timedelta

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import connection
from django.test import Client as WebClient, RequestFactory
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from delivery_bookings.models import Booking
from delivery_bookings.services import find_available_couriers
from delivery_bookings.views import booking_detail, booking_list
from delivery_orders.models import Order
from delivery_routes.models import Route
from db.import_json import import_data
from homepage.models import Client, Courier


def test_admin_registration_search_inline_and_status_change(rollback_orm):
    assert all(
        model in admin.site._registry
        for model in (Client, Courier, Order, Route, Booking)
    )
    user = get_user_model().objects.create_superuser(
        username="pr10_admin",
        email="pr10@example.test",
        password="temporary-test-key",
    )
    browser = WebClient(HTTP_HOST="localhost")
    browser.force_login(user)
    booking = Booking.objects.create(
        order_id=3, courier_id=3, delivery_date=date(2027, 3, 1)
    )
    changelist = reverse("admin:delivery_bookings_booking_changelist")
    assert browser.get(changelist, {"q": "Кремль"}).status_code == 200
    assert (
        browser.get(changelist, {"status__exact": "active"}).status_code == 200
    )
    courier_page = browser.get(
        reverse("admin:homepage_courier_change", args=[3])
    )
    assert courier_page.status_code == 200
    assert b"bookings-0-status" in courier_page.content
    change_url = reverse(
        "admin:delivery_bookings_booking_change", args=[booking.pk]
    )
    response = browser.post(
        change_url,
        {
            "order": 3,
            "courier": 3,
            "delivery_date": "2027-03-01",
            "status": Booking.Status.COMPLETED,
            "_save": "Сохранить",
        },
    )
    assert response.status_code == 302
    booking.refresh_from_db()
    assert booking.status == Booking.Status.COMPLETED
    assert Courier.objects.get(pk=3) in find_available_couriers(
        date(2027, 3, 1), 60
    )


def test_booking_filters_pagination_and_related_query(rollback_orm):
    client = Client.objects.get(pk=1)
    courier = Courier.objects.get(pk=3)
    start = date(2027, 4, 1)
    bookings = []
    for index in range(8):
        order = Order.objects.create(
            destination=f"Проверочный адрес {index}",
            weight=1,
            client=client,
            status=Order.STATUS_CREATED,
        )
        bookings.append(
            Booking.objects.create(
                order=order,
                courier=courier,
                delivery_date=start + timedelta(days=index),
            )
        )
    bookings[0].cancel()
    bookings[1].status = Booking.Status.COMPLETED
    bookings[1].save(update_fields=["status"])
    assert Booking.objects.active().count() == 6
    assert Booking.objects.cancelled().count() == 1
    assert Booking.objects.completed().count() == 1
    assert Booking.objects.for_date(start).count() == 1
    assert courier in find_available_couriers(start, 1)
    assert courier not in find_available_couriers(start + timedelta(days=2), 1)

    browser = WebClient(HTTP_HOST="localhost")
    response = browser.get(
        "/bookings/",
        {
            "status": "active",
            "courier": str(courier.pk),
            "sort": "date",
            "page": "2",
        },
    )
    html = response.content.decode("utf-8")
    assert response.status_code == 200
    assert "djDebugToolbar" in html
    assert "Страница 2 из 2" in html
    assert "status=active" in html and "sort=date" in html
    assert "Проверочный адрес 7" in html
    assert "— Проверочный адрес 0" not in html
    assert "— Проверочный адрес 1" not in html
    filtered = browser.get(
        "/bookings/",
        {
            "date": start.isoformat(),
            "courier": str(courier.pk),
            "order": str(bookings[0].order_id),
            "status": "cancelled",
        },
    )
    assert "Проверочный адрес 0" in filtered.content.decode("utf-8")
    assert browser.get(f"/bookings/{bookings[0].pk}/").status_code == 200
    assert browser.get("/bookings/999999/").status_code == 404

    with CaptureQueriesContext(connection) as queries:
        booking = Booking.objects.select_related(
            "order", "order__client", "courier"
        ).get(pk=bookings[0].pk)
        assert booking.order.client.name == client.name
        assert booking.courier.name == courier.name
    assert len(queries) == 1
    factory = RequestFactory()
    with CaptureQueriesContext(connection) as detail_queries:
        assert (
            booking_detail(
                factory.get(f"/bookings/{bookings[0].pk}/"), bookings[0].pk
            ).status_code
            == 200
        )
    assert len(detail_queries) <= 2
    with CaptureQueriesContext(connection) as list_queries:
        assert (
            booking_list(factory.get("/bookings/?status=active")).status_code
            == 200
        )
    assert len(list_queries) <= 5


def test_route_slug_and_global_context(rollback_orm):
    route = Route.objects.get(pk=1)
    assert route.slug == "marshrut-1"
    browser = WebClient(HTTP_HOST="localhost")
    assert browser.get(route.get_absolute_url()).status_code == 200
    assert browser.get("/routes/by-slug/unknown/").status_code == 404
    assert browser.get("/routes/1/").status_code == 200
    Courier.objects.create(name="Временный курьер", capacity=10)
    assert "Свободные курьеры (4)" in browser.get("/").content.decode("utf-8")


def test_cancelled_bookings_survive_status_migration(tmp_path):
    database = tmp_path / "migration.sqlite3"
    environment = dict(
        os.environ, DJANGO_DB_PATH=str(database), DJANGO_DEBUG="0"
    )
    command = [sys.executable, str(settings.BASE_DIR / "manage.py"), "migrate"]
    subprocess.run(
        command + ["delivery_bookings", "0001"],
        cwd=settings.BASE_DIR,
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )
    with sqlite3.connect(database) as db:
        db.execute("INSERT INTO homepage_client VALUES (1, 'Тест', '+7')")
        db.execute("INSERT INTO homepage_courier VALUES (1, 'Курьер', 50, 1)")
        db.execute(
            "INSERT INTO delivery_orders_order "
            "(id, destination, weight, client_id, courier_id, status) "
            "VALUES (1, 'Адрес', 1, 1, NULL, 'создан')"
        )
        db.execute(
            "INSERT INTO delivery_bookings_booking "
            "(id, delivery_date, is_cancelled, order_id, courier_id) "
            "VALUES (1, '2027-05-01', 1, 1, 1)"
        )
    subprocess.run(
        command + ["delivery_bookings"],
        cwd=settings.BASE_DIR,
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )
    with sqlite3.connect(database) as db:
        assert (
            db.execute(
                "SELECT status FROM delivery_bookings_booking WHERE id = 1"
            ).fetchone()[0]
            == Booking.Status.CANCELLED
        )
        columns = {
            row[1]
            for row in db.execute(
                "PRAGMA table_info(delivery_bookings_booking)"
            )
        }
        assert "is_cancelled" not in columns


def test_legacy_import_maps_booking_statuses(tmp_path):
    source = tmp_path / "legacy.sqlite"
    target = tmp_path / "django.sqlite3"
    import_data(db_path=source)
    with sqlite3.connect(source) as db:
        db.executemany(
            "INSERT INTO courier_bookings "
            "(id, order_id, courier_id, delivery_date, is_cancelled) "
            "VALUES (?, ?, ?, ?, ?)",
            [(1, 3, 3, "2027-06-01", 1), (2, 4, 3, "2027-06-02", 0)],
        )
    environment = dict(
        os.environ, DJANGO_DB_PATH=str(target), DJANGO_DEBUG="0"
    )
    command = [sys.executable, str(settings.BASE_DIR / "manage.py")]
    for arguments in (
        ["migrate"],
        ["import_legacy_data", "--source", str(source)],
    ):
        subprocess.run(
            command + arguments,
            cwd=settings.BASE_DIR,
            env=environment,
            capture_output=True,
            text=True,
            check=True,
        )
    with sqlite3.connect(target) as db:
        assert db.execute(
            "SELECT id, status FROM delivery_bookings_booking ORDER BY id"
        ).fetchall() == [(1, "cancelled"), (2, "active")]
        assert db.execute(
            "SELECT slug FROM delivery_routes_route ORDER BY id"
        ).fetchall() == [("marshrut-1",), ("marshrut-2",)]
