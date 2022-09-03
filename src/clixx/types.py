from abc import ABCMeta, abstractmethod
from typing import Any

from .exceptions import DefinitionError, UsageError


class TypeBase(metaclass=ABCMeta):
    def __call__(self, value: Any) -> Any:
        if value is None:
            return None
        return self.convert(value)

    @abstractmethod
    def convert(self, value: Any) -> Any:
        ...


class Identity(TypeBase):
    def convert(self, value: Any) -> Any:
        return value


class Str(TypeBase):
    def convert(self, value: Any) -> Any:
        return str(value)


class Int(TypeBase):
    def __init__(self, *, base: int = 10) -> None:
        if not (2 <= base <= 36 or base == 0):
            raise DefinitionError(f"Require 2 <= base <= 36 or base == 0, got {base!r}.")
        self.base = base

    def convert(self, value: Any) -> Any:
        try:
            return int(value, base=self.base)
        except ValueError:
            if self.base in {0, 10}:
                raise UsageError(f"{value!r} is not a valid int.")
            else:
                raise UsageError(f"{value!r} is not a valid int with base {self.base!r}.")


class Float(TypeBase):
    def convert(self, value: Any) -> Any:
        try:
            return float(value)
        except ValueError:
            raise UsageError(f"{value!r} is not a valid float.")
