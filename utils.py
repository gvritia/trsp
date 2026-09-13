"""Вспомогательные функции безопасного ввода."""


def input_int(prompt: str, minimum: int | None = None) -> int:
    """Запросить целое число и повторять ввод при ошибке."""
    while True:
        try:
            value = int(input(prompt))
            if minimum is not None and value < minimum:
                raise ValueError
            return value
        except ValueError:
            suffix = f" не меньше {minimum}" if minimum is not None else ""
            print(f"Введите целое число{suffix}.")


def input_float(prompt: str, minimum: float | None = None) -> float:
    """Запросить вещественное число и повторять ввод при ошибке."""
    while True:
        try:
            value = float(input(prompt).replace(",", "."))
            if minimum is not None and value < minimum:
                raise ValueError
            return value
        except ValueError:
            suffix = f" не меньше {minimum:g}" if minimum is not None else ""
            print(f"Введите число{suffix}.")
