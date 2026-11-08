"""Администрирование клиентов и курьеров."""

from django.contrib import admin

from delivery_bookings.models import Booking
from .models import Client, Courier


class CourierBookingInline(admin.TabularInline):
    model = Booking
    extra = 0
    fields = ("order", "delivery_date", "status")
    show_change_link = True


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "phone")
    search_fields = ("name", "phone")
    ordering = ("name",)
    list_per_page = 20


@admin.register(Courier)
class CourierAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "capacity", "active")
    search_fields = ("name",)
    list_filter = ("active",)
    ordering = ("name",)
    list_per_page = 20
    inlines = (CourierBookingInline,)
