"""ПР7, 7.2 №24–25, №27: страницы бронирований и поиска курьеров."""

from django.urls import path

from . import views

app_name = "delivery_bookings"

urlpatterns = [
    path("", views.booking_list, name="list"),
    path("available/", views.available_couriers, name="available"),
    path("create/", views.create_booking, name="create"),
    path("<int:booking_id>/cancel/", views.cancel, name="cancel"),
]
