"""Страницы просмотра существующих маршрутов доставки."""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from models.routes import get_route
from storage import load_delivery_data


def route_list(request: HttpRequest) -> HttpResponse:
    """Показать маршруты из JSON-хранилища по возрастанию ID."""
    _, _, _, routes = load_delivery_data(settings.BASE_DIR / "data")
    # sorted создаёт новый список и не изменяет загруженные объекты.
    context = {"routes": sorted(routes, key=lambda route: route.id)}
    return render(request, "delivery_routes/route_list.html", context)


def route_detail(request: HttpRequest, route_id: int) -> HttpResponse:
    """Показать найденный маршрут или шаблон с кодом HTTP 404."""
    _, _, _, routes = load_delivery_data(settings.BASE_DIR / "data")
    try:
        # Маршрут ищем существующей функцией предметной области.
        route = get_route(routes, route_id)
    except ValueError:
        # Тот же шаблон 404 используется и для заказов, и для маршрутов.
        context = {
            "page_title": "Маршрут не найден",
            "message": f"Маршрут с ID {route_id} не найден.",
            "back_url_name": "delivery_routes:list",
            "back_label": "К списку маршрутов",
        }
        return render(
            request, "homepage/not_found.html", context, status=404
        )

    return render(
        request, "delivery_routes/route_detail.html", {"route": route}
    )


def invalid_route_id(request: HttpRequest, route_id: str) -> HttpResponse:
    """Показать отдельную ошибку для нечислового ID маршрута."""
    context = {
        "page_title": "Некорректный ID маршрута",
        "message": "ID маршрута должен быть целым неотрицательным числом.",
        "back_url_name": "delivery_routes:list",
        "back_label": "К списку маршрутов",
    }
    return render(request, "homepage/not_found.html", context, status=404)
