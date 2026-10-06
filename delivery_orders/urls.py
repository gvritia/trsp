"""Маршруты страниц заказов."""

from django.urls import path

from . import views

app_name = "delivery_orders"

urlpatterns = [
    path("", views.order_list, name="list"),
    path("<int:order_id>/", views.order_detail, name="detail"),
]
