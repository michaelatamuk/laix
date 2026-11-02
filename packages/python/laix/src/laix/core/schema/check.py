"""Minimal structural validation against the generated record schema."""

from __future__ import annotations

from typing import Any

from .build import build_schema


def check(record_name: str, payload: dict[str, Any]) -> list[str]:
    """Minimal structural validation.

    This is intentionally not a general JSON Schema implementation.  It checks
    required keys, primitive types and enums for the committed records so the
    package stays standard-library only.
    """
    document = build_schema()
    definition = document["$defs"].get(record_name)
    if definition is None:
        return [f"unknown record: {record_name}"]
    errors: list[str] = []
    for key in definition["required"]:
        if key not in payload:
            errors.append(f"missing required field: {key}")
    for key, value in payload.items():
        spec = definition["properties"].get(key)
        if spec is None:
            errors.append(f"unknown field: {key}")
            continue
        expected = _expected_type(spec)
        if expected and not _matches(value, expected):
            errors.append(f"{key}: expected {expected}, got {type(value).__name__}")
        enum = spec.get("enum")
        if enum and value not in enum:
            errors.append(f"{key}: {value!r} is not one of {enum}")
    return errors


def _expected_type(spec: dict[str, Any]) -> str | None:
    if "anyOf" in spec:
        for item in spec["anyOf"]:
            if item.get("type") != "null":
                return item.get("type")
        return None
    return spec.get("type")


def _matches(value: Any, expected: str) -> bool:
    if value is None:
        return True
    return {
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "object": isinstance(value, dict),
        "array": isinstance(value, (list, tuple)),
    }.get(expected, True)


__all__ = ["check"]
