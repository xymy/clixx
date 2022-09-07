from typing import Any

from .exceptions import DefinitionError


class Type:
    def __call__(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            return self.convert_str(value)
        return self.convert(value)

    def convert(self, value: Any) -> Any:
        return value

    def convert_str(self, value: str) -> Any:
        return value


class Str(Type):
    def convert(self, value: Any) -> Any:
        raise ValueError(f"{value!r} is not a valid str.")

    def convert_str(self, value: str) -> Any:
        return value


class Int(Type):
    def __init__(self, *, base: int = 10) -> None:
        if not (2 <= base <= 36 or base == 0):
            raise DefinitionError(f"Require 2 <= base <= 36 or base == 0, got {base!r}.")
        self.base = base

    def convert(self, value: Any) -> Any:
        if isinstance(value, int):
            return value
        raise ValueError(f"{value!r} is not a valid int.")

    def convert_str(self, value: str) -> Any:
        try:
            return int(value, base=self.base)
        except ValueError:
            if self.base in {0, 10}:
                raise ValueError(f"{value!r} is not a valid int.")
            else:
                raise ValueError(f"{value!r} is not a valid int with base {self.base!r}.")


class Float(Type):
    def convert(self, value: Any) -> Any:
        if isinstance(value, float):
            return value
        raise ValueError(f"{value!r} is not a valid float.")

    def convert_str(self, value: str) -> Any:
        try:
            return float(value)
        except ValueError:
            raise ValueError(f"{value!r} is not a valid float.")
