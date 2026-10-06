"""Страницы чтения существующих заказов доставки."""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.html import escape

from homepage.views import page
from models.orders import get_order, get_order_status, sort_orders
from storage import load_delivery_data


def order_list(request: HttpRequest) -> HttpResponse:
    """Показать список реальных заказов из JSON-хранилища."""
    _, _, orders, _ = load_delivery_data(settings.BASE_DIR / "data")
    if not orders:
        content = '<div class="alert alert-info">Заказов пока нет.</div>'
    else:
        rows = []
        for order in sort_orders(orders, key="id"):
            detail_url = reverse(
                "delivery_orders:detail", args=[order.id]
            )
            rows.append(
                "<tr>"
                f'<th scope="row"><a href="{detail_url}">#{order.id}</a></th>'
                f"<td>{escape(order.destination)}</td>"
                f"<td>{escape(order.client.name)}</td>"
                f"<td>{order.weight:g} кг</td>"
                f"<td>{escape(order.status)}</td>"
                "</tr>"
            )
        content = (
            '<div class="table-responsive"><table class="table '
            'table-striped align-middle">'
            "<thead><tr><th>ID</th><th>Адрес</th><th>Клиент</th>"
            "<th>Вес</th><th>Статус</th></tr></thead><tbody>"
            + "".join(rows)
            + "</tbody></table></div>"
        )
    return HttpResponse(page("Заказы", content))


def order_detail(request: HttpRequest, order_id: int) -> HttpResponse:
    """Показать заказ по ID или вернуть оформленный HTTP 404."""
    _, _, orders, _ = load_delivery_data(settings.BASE_DIR / "data")
    list_url = reverse("delivery_orders:list")
    try:
        order = get_order(orders, order_id)
    except ValueError:
        content = (
            '<div class="alert alert-warning">Заказ не найден.</div>'
            f'<a class="btn btn-primary" href="{list_url}">'
            "К списку заказов</a>"
        )
        return HttpResponse(
            page("Заказ не найден", content), status=404
        )

    courier_name = order.courier.name if order.courier else "Не назначен"
    content = f"""
<div class="card mb-3"><div class="card-body">
  <dl class="row mb-0">
    <dt class="col-sm-4">ID</dt><dd class="col-sm-8">{order.id}</dd>
    <dt class="col-sm-4">Адрес</dt>
    <dd class="col-sm-8">{escape(order.destination)}</dd>
    <dt class="col-sm-4">Вес</dt>
    <dd class="col-sm-8">{order.weight:g} кг</dd>
    <dt class="col-sm-4">Клиент</dt>
    <dd class="col-sm-8">{escape(order.client.name)}</dd>
    <dt class="col-sm-4">Курьер</dt>
    <dd class="col-sm-8">{escape(courier_name)}</dd>
    <dt class="col-sm-4">Статус</dt>
    <dd class="col-sm-8">{escape(order.status)}</dd>
  </dl>
</div></div>
<p>{escape(get_order_status(order))}</p>
<a class="btn btn-outline-primary" href="{list_url}">К списку заказов</a>"""
    return HttpResponse(page(f"Заказ #{order.id}", content))
