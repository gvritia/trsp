"""Общий HTML-каркас, главная страница и страница 404."""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.html import escape

from models.orders import calculate_efficiency
from storage import load_delivery_data


def page(title: str, content: str) -> str:
    """Сформировать общий адаптивный HTML-документ для страниц проекта."""
    home_url = reverse("homepage:index")
    orders_url = reverse("delivery_orders:list")
    routes_url = reverse("delivery_routes:list")
    bootstrap_url = (
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/"
        "bootstrap.min.css"
    )
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} — Система доставки</title>
  <link href="{bootstrap_url}" rel="stylesheet">
</head>
<body class="bg-light">
  <nav class="navbar navbar-expand-md navbar-dark bg-primary">
    <div class="container">
      <a class="navbar-brand" href="{home_url}">Система доставки</a>
      <div class="navbar-nav flex-row gap-3">
        <a class="nav-link text-white" href="{home_url}">Главная</a>
        <a class="nav-link text-white" href="{orders_url}">Заказы</a>
        <a class="nav-link text-white" href="{routes_url}">Маршруты</a>
      </div>
    </div>
  </nav>
  <main class="container py-4">
    <h1 class="h2 mb-4">{escape(title)}</h1>
    {content}
  </main>
</body>
</html>"""


def index(request: HttpRequest) -> HttpResponse:
    """Показать стартовую страницу с показателями из текущих JSON-данных."""
    clients, couriers, orders, routes = load_delivery_data(
        settings.BASE_DIR / "data"
    )
    efficiency = calculate_efficiency(orders)
    orders_url = reverse("delivery_orders:list")
    routes_url = reverse("delivery_routes:list")
    content = f"""
<p class="lead">Просмотр заказов и маршрутов из существующего проекта
планирования доставки. Данные загружаются из JSON-файлов.</p>
<div class="row g-3 mb-4">
  <div class="col-sm-6 col-lg-3"><div class="card h-100">
    <div class="card-body">
    <div class="text-muted">Заказы</div><div class="fs-3">{len(orders)}</div>
  </div></div></div>
  <div class="col-sm-6 col-lg-3"><div class="card h-100">
    <div class="card-body">
    <div class="text-muted">Маршруты</div><div class="fs-3">{len(routes)}</div>
  </div></div></div>
  <div class="col-sm-6 col-lg-3"><div class="card h-100">
    <div class="card-body">
    <div class="text-muted">Клиенты</div><div class="fs-3">{len(clients)}</div>
  </div></div></div>
  <div class="col-sm-6 col-lg-3"><div class="card h-100">
    <div class="card-body">
    <div class="text-muted">Курьеры</div>
    <div class="fs-3">{len(couriers)}</div>
  </div></div></div>
</div>
<p>Назначено активных заказов: <strong>{efficiency:.1f}%</strong>.</p>
<div class="d-flex flex-wrap gap-2">
  <a class="btn btn-primary" href="{orders_url}">Смотреть заказы</a>
  <a class="btn btn-outline-primary" href="{routes_url}">Смотреть маршруты</a>
</div>"""
    return HttpResponse(page("Главная", content))


def page_not_found(
    request: HttpRequest, exception: Exception
) -> HttpResponse:
    """Показать общую страницу для неизвестного URL."""
    home_url = reverse("homepage:index")
    content = (
        '<div class="alert alert-warning" role="alert">'
        "Такой страницы нет.</div>"
        f'<a class="btn btn-primary" href="{home_url}">На главную</a>'
    )
    return HttpResponse(page("Страница не найдена", content), status=404)
