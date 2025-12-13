"""Validation utilities for Quark state."""

from typing import Callable, Generic, Optional

from ..atom import Quark
from ..types import T


class ValidationError(ValueError):
    """Raised when validation fails."""

    pass


class ValidatedQuark(Quark[T], Generic[T]):
    """Quark that validates values before setting."""

    __slots__ = ("_validator", "_on_invalid")

    def __init__(
        self,
        initial: T,
        validator: Callable[[T], bool],
        on_invalid: Optional[Callable[[T], T]] = None,
    ) -> None:
        if not validator(initial):
            raise ValidationError(f"Initial value failed validation: {initial}")
        super().__init__(initial)
        self._validator = validator
        self._on_invalid = on_invalid

    def set_sync(self, new_value: T) -> None:
        if self._validator(new_value):
            super().set_sync(new_value)
        elif self._on_invalid:
            super().set_sync(self._on_invalid(new_value))
        else:
            raise ValidationError(f"Value failed validation: {new_value}")

    async def set(self, new_value: T) -> None:
        if self._validator(new_value):
            await super().set(new_value)
        elif self._on_invalid:
            await super().set(self._on_invalid(new_value))
        else:
            raise ValidationError(f"Value failed validation: {new_value}")


def validate(
    initial: T,
    validator: Callable[[T], bool],
    on_invalid: Optional[Callable[[T], T]] = None,
) -> ValidatedQuark[T]:
    """Create a Quark with value validation."""
    return ValidatedQuark(initial, validator, on_invalid)


def in_range(min_val: float, max_val: float) -> Callable[[float], bool]:
    """Create a range validator."""
    return lambda x: min_val <= x <= max_val


def clamp(min_val: float, max_val: float) -> Callable[[float], float]:
    """Create a clamping function for on_invalid."""
    return lambda x: max(min_val, min(max_val, x))
