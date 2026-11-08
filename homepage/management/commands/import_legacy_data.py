"""Разовый перенос предметных данных из прежней SQLite (или исходных JSON)."""

import json
import sqlite3
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from delivery_bookings.models import Booking
from delivery_orders.models import Order
from delivery_routes.models import Route, RouteOrder
from homepage.models import Client, Courier


def read_source(source: Path):
    if source.is_file():
        with sqlite3.connect(
            f"file:{source.as_posix()}?mode=ro", uri=True
        ) as db:
            db.row_factory = sqlite3.Row
            tables = {
                row[0]
                for row in db.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            required = {
                "clients",
                "couriers",
                "orders",
                "routes",
                "route_orders",
            }
            if not required.issubset(tables):
                raise CommandError(
                    "Исходная SQLite не содержит все предметные таблицы."
                )
            rows = {
                name: [
                    dict(row) for row in db.execute(f"SELECT * FROM {name}")
                ]
                for name in required
            }
            rows["bookings"] = (
                [
                    dict(row)
                    for row in db.execute("SELECT * FROM courier_bookings")
                ]
                if "courier_bookings" in tables
                else []
            )
            return rows
    data_dir = Path(settings.BASE_DIR) / "data"
    rows = {}
    for name in ("clients", "couriers", "orders", "routes"):
        path = data_dir / f"{name}.json"
        if not path.is_file():
            raise CommandError(f"Нет файла данных: {path}")
        rows[name] = json.loads(path.read_text(encoding="utf-8"))
    rows["route_orders"] = [
        {"route_id": route["id"], "order_id": order_id}
        for route in rows["routes"]
        for order_id in route["order_ids"]
    ]
    rows["bookings"] = []
    return rows


class Command(BaseCommand):
    help = (
        "Перенести прежние данные в модели Django; "
        "при отсутствии SQLite использовать JSON."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--source", type=Path, default=None, help="Путь к прежней SQLite"
        )

    def handle(self, *args, **options):
        if any(
            model.objects.exists()
            for model in (Client, Courier, Order, Route, Booking)
        ):
            raise CommandError(
                "База ORM уже содержит данные; перенос отменён во избежание перезаписи."
            )
        source = (
            options["source"]
            or Path(settings.BASE_DIR) / "data" / "delivery.sqlite"
        )
        if options["source"] is not None and not source.is_file():
            raise CommandError(f"Исходная SQLite не найдена: {source}")
        rows = read_source(source)
        try:
            with transaction.atomic():
                Client.objects.bulk_create(
                    [Client(**row) for row in rows["clients"]]
                )
                Courier.objects.bulk_create(
                    [Courier(**row) for row in rows["couriers"]]
                )
                Order.objects.bulk_create(
                    [Order(**row) for row in rows["orders"]]
                )
                Route.objects.bulk_create(
                    [
                        Route(
                            id=row["id"], status=row["status"],
                            slug=f"marshrut-{row['id']}",
                        )
                        for row in rows["routes"]
                    ]
                )
                for row in rows["route_orders"]:
                    RouteOrder.objects.create(**row)
                Booking.objects.bulk_create(
                    [
                        Booking(
                            id=row["id"], order_id=row["order_id"],
                            courier_id=row["courier_id"],
                            delivery_date=row["delivery_date"],
                            status=(
                                Booking.Status.CANCELLED
                                if row["is_cancelled"]
                                else Booking.Status.ACTIVE
                            ),
                        )
                        for row in rows["bookings"]
                    ]
                )
        except Exception as exc:
            raise CommandError(f"Перенос отменён: {exc}") from exc
        self.stdout.write(
            self.style.SUCCESS(
                f"Перенесено: клиентов {len(rows['clients'])}, "
                f"курьеров {len(rows['couriers'])}, заказов {len(rows['orders'])}, "
                f"маршрутов {len(rows['routes'])}, "
                f"бронирований {len(rows['bookings'])}."
            )
        )
