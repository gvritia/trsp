"""Администрирование заказов и связанных бронирований."""

from django.contrib import admin

from delivery_bookings.models import Booking
from .models import Order


class OrderBookingInline(admin.TabularInline):
    model = Booking
    extra = 0
    fields = ("courier", "delivery_date", "status")
    show_change_link = True


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "destination",
        "client",
        "courier",
        "weight",
        "status",
    )
    search_fields = ("destination", "client__name", "courier__name")
    list_filter = ("status", "courier")
    list_select_related = ("client", "courier")
    ordering = ("-id",)
    list_per_page = 20
    inlines = (OrderBookingInline,)
