"""Маршруты страниц доставки."""

from django.urls import path

from . import views

app_name = "delivery_routes"

urlpatterns = [
    path("", views.route_list, name="list"),
    path("<int:route_id>/", views.route_detail, name="detail"),
]
