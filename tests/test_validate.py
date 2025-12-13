"""Tests for validation utilities."""

import pytest

from statequark import ValidationError, clamp, in_range, validate


class TestValidate:
    def test_valid_value(self):
        q = validate(50, in_range(0, 100))
        q.set_sync(75)
        assert q.value == 75

    def test_invalid_raises(self):
        q = validate(50, in_range(0, 100))
        with pytest.raises(ValidationError):
            q.set_sync(150)

    def test_clamp_on_invalid(self):
        q = validate(50, in_range(0, 100), clamp(0, 100))
        q.set_sync(150)
        assert q.value == 100
        q.set_sync(-10)
        assert q.value == 0

    def test_invalid_initial_raises(self):
        with pytest.raises(ValidationError):
            validate(150, in_range(0, 100))
