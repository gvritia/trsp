"""Базовые классы участников системы доставки."""

from abc import ABC, abstractmethod
from typing import Any


class Person(ABC):
    """Абстрактный участник системы с идентификатором и именем."""

    def __init__(self, person_id: int, name: str) -> None:
        if person_id < 1:
            raise ValueError("идентификатор должен быть положительным")
        name = name.strip()
        if not name:
            raise ValueError("имя не может быть пустым")
        self.id = person_id
        self.name = name

    @property
    @abstractmethod
    def role(self) -> str:
        """Вернуть название роли участника."""

    @abstractmethod
    def to_data(self) -> dict[str, Any]:
        """Преобразовать объект в данные для JSON."""

    def __str__(self) -> str:
        """Вернуть полиморфное строковое представление участника."""
        return f"{self.role} #{self.id}: {self.name}"
