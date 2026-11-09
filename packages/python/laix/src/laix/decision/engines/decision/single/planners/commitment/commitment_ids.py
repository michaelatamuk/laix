"""Normalise commitment identifiers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def _ids(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Mapping):
        return (str(value.get("id", value)),)
    if isinstance(value, Iterable):
        return tuple(
            str(item.get("id", item)) if isinstance(item, Mapping) else str(item)
            for item in value
        )
    return (str(value),)


__all__ = ["_ids"]
