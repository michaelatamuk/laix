"""The declared public surface resolves."""

from __future__ import annotations

import laix
import laix.core


def test_top_level_exports_resolve() -> None:
    for name in laix.__all__:
        assert hasattr(laix, name), f"laix.__all__ contains missing name: {name}"


def test_core_exports_resolve() -> None:
    for name in laix.core.__all__:
        assert hasattr(laix.core, name), f"laix.core.__all__ contains missing name: {name}"
