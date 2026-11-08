"""Маршрут главной страницы."""

from django.urls import path

from . import views

# Пространство имён позволяет ссылаться на страницу как homepage:index.
app_name = "homepage"

urlpatterns = [
    path("", views.index, name="index"),
    # ПР7, чек-лист 7.2 №26–27: страница статистики и её именованный URL.
    path("statistics/", views.statistics, name="statistics"),
]
