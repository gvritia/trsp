"""Тесты функций работы с клиентами."""

import pytest

from clients import add_client, find_clients, get_client


def test_add_and_find_client() -> None:
    clients = []

    client = add_client(clients, "Анна Смирнова", "+7-900-111-22-33")

    assert get_client(clients, client["id"]) == client
    assert find_clients(clients, "смирнова") == [client]


def test_duplicate_phone_is_rejected() -> None:
    clients = []
    add_client(clients, "Анна Смирнова", "+7-900-111-22-33")

    with pytest.raises(ValueError, match="телефоном"):
        add_client(clients, "Анна Петрова", "+7-900-111-22-33")
