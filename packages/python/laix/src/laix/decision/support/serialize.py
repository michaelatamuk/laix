"""Recursive conversion of records to JSON-compatible primitives."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any


def to_primitive(value: Any) -> Any:
    """Recursively convert a contract (or a container of them) to JSON types."""
    if is_dataclass(value) and not isinstance(value, type):
        return {key: to_primitive(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): to_primitive(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_primitive(item) for item in value]
    return value


def to_string_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(str(item) for item in value)


__all__ = ["to_primitive", "to_string_tuple"]
