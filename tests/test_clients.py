"""Тесты объектной модели клиентов."""

import pytest

from models import Client, Person
from models.clients import add_client, find_clients, get_client


def test_client_creation_and_string_representation() -> None:
    client = Client(1, "Анна Смирнова", "+7-900-111-22-33")

    assert isinstance(client, Person)
    assert client.id == 1
    assert client.phone == "+7-900-111-22-33"
    assert "Клиент #1" in str(client)


def test_add_and_find_client_objects() -> None:
    clients: list[Client] = []

    client = add_client(clients, "Анна Смирнова", "+7-900-111-22-33")

    assert get_client(clients, client.id) is client
    assert find_clients(clients, "смирнова") == [client]


def test_duplicate_phone_is_rejected() -> None:
    clients: list[Client] = []
    add_client(clients, "Анна Смирнова", "+7-900-111-22-33")

    with pytest.raises(ValueError, match="телефоном"):
        add_client(clients, "Анна Петрова", "+7-900-111-22-33")
