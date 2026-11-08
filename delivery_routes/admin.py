"""Администрирование маршрутов и состава заказов."""

from django.contrib import admin

from .models import Route, RouteOrder


class RouteOrderInline(admin.TabularInline):
    model = RouteOrder
    extra = 0
    fields = ("order",)
    autocomplete_fields = ("order",)


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ("id", "slug", "status")
    list_filter = ("status",)
    search_fields = ("slug",)
    ordering = ("id",)
    list_per_page = 20
    inlines = (RouteOrderInline,)
