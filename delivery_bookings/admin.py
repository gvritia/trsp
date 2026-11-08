"""Поиск и изменение статусов бронирования в Django Admin."""

from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "courier", "delivery_date", "status")
    search_fields = (
        "order__destination",
        "order__client__name",
        "courier__name",
    )
    list_filter = ("status", "delivery_date", "courier")
    list_select_related = ("order", "courier")
    ordering = ("-delivery_date", "-id")
    list_per_page = 20
    autocomplete_fields = ("order", "courier")
