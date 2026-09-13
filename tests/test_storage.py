"""Тесты JSON-хранилища."""

from pathlib import Path

import pytest

from storage import load_records, save_records


def test_json_round_trip(tmp_path: Path) -> None:
    file_path = tmp_path / "nested" / "orders.json"
    records = [{"id": 1, "destination": "Москва"}]

    save_records(file_path, records)

    assert load_records(file_path) == records


def test_invalid_json_is_reported(tmp_path: Path) -> None:
    file_path = tmp_path / "orders.json"
    file_path.write_text("not json", encoding="utf-8")

    with pytest.raises(ValueError, match="повреждён JSON"):
        load_records(file_path)
