"""Маршрут главной страницы."""

from django.urls import path

from . import views

# Пространство имён позволяет ссылаться на страницу как homepage:index.
app_name = "homepage"

urlpatterns = [path("", views.index, name="index")]
