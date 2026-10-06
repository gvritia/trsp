"""Страницы чтения существующих маршрутов доставки."""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.html import escape

from homepage.views import page
from models.routes import get_route
from storage import load_delivery_data


def route_list(request: HttpRequest) -> HttpResponse:
    """Показать список реальных маршрутов из JSON-хранилища."""
    _, _, _, routes = load_delivery_data(settings.BASE_DIR / "data")
    if not routes:
        content = '<div class="alert alert-info">Маршрутов пока нет.</div>'
    else:
        rows = []
        for route in sorted(routes, key=lambda item: item.id):
            detail_url = reverse(
                "delivery_routes:detail", args=[route.id]
            )
            rows.append(
                "<tr>"
                f'<th scope="row"><a href="{detail_url}">#{route.id}</a>'
                "</th>"
                f"<td>{escape(route.courier.name)}</td>"
                f"<td>{len(route.orders)}</td>"
                f"<td>{escape(route.status)}</td>"
                "</tr>"
            )
        content = (
            '<div class="table-responsive"><table class="table '
            'table-striped align-middle">'
            "<thead><tr><th>ID</th><th>Курьер</th><th>Заказов</th>"
            "<th>Статус</th></tr></thead><tbody>"
            + "".join(rows)
            + "</tbody></table></div>"
        )
    return HttpResponse(page("Маршруты", content))


def route_detail(request: HttpRequest, route_id: int) -> HttpResponse:
    """Показать маршрут по ID или вернуть оформленный HTTP 404."""
    _, _, _, routes = load_delivery_data(settings.BASE_DIR / "data")
    list_url = reverse("delivery_routes:list")
    try:
        route = get_route(routes, route_id)
    except ValueError:
        content = (
            '<div class="alert alert-warning">Маршрут не найден.</div>'
            f'<a class="btn btn-primary" href="{list_url}">'
            "К списку маршрутов</a>"
        )
        return HttpResponse(
            page("Маршрут не найден", content), status=404
        )

    order_links = []
    for order in route.orders:
        order_url = reverse("delivery_orders:detail", args=[order.id])
        order_links.append(
            '<li class="list-group-item">'
            f'<a href="{order_url}">Заказ #{order.id}</a> — '
            f"{escape(order.destination)}"
            "</li>"
        )
    content = f"""
<div class="card mb-3"><div class="card-body">
  <dl class="row mb-0">
    <dt class="col-sm-4">ID</dt><dd class="col-sm-8">{route.id}</dd>
    <dt class="col-sm-4">Курьер</dt>
    <dd class="col-sm-8">{escape(route.courier.name)}</dd>
    <dt class="col-sm-4">Статус</dt>
    <dd class="col-sm-8">{escape(route.status)}</dd>
  </dl>
</div></div>
<h2 class="h4">Заказы маршрута</h2>
<ul class="list-group mb-3">{"".join(order_links)}</ul>
<a class="btn btn-outline-primary" href="{list_url}">
  К списку маршрутов
</a>"""
    return HttpResponse(page(f"Маршрут #{route.id}", content))
