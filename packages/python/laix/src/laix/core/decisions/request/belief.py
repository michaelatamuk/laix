"""A proposition the layer currently holds, with confidence and an expiry."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from ...support.serialize import to_primitive, to_string_tuple
from ...support.time import iso, parse_iso, utcnow
from ...support.values import clamp, confidence_band
from ...support.version import SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class Belief:
    """A proposition the layer currently holds, with confidence and an expiry."""

    id: str
    proposition: str
    confidence: float
    evidence: tuple[str, ...] = ()
    updated_at: str = field(default_factory=iso)
    expires_at: str | None = None
    source: str = "observation"
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "confidence", clamp(self.confidence))
        object.__setattr__(self, "evidence", to_string_tuple(self.evidence))

    @property
    def band(self) -> str:
        return confidence_band(self.confidence)

    def expired(self, now: datetime | None = None) -> bool:
        expires = parse_iso(self.expires_at)
        return bool(expires and expires <= (now or utcnow()))

    def decayed(self, now: datetime | None = None, half_life_minutes: float = 720.0) -> float:
        updated = parse_iso(self.updated_at)
        if not updated or half_life_minutes <= 0:
            return self.confidence
        elapsed = ((now or utcnow()) - updated).total_seconds() / 60.0
        if elapsed <= 0:
            return self.confidence
        return clamp(self.confidence * (0.5 ** (elapsed / half_life_minutes)))

    def to_dict(self) -> dict:
        payload = to_primitive(self)
        payload["band"] = self.band
        return payload

    @classmethod
    def from_dict(cls, payload: dict) -> "Belief":
        data = dict(payload)
        data.pop("band", None)
        if "evidence" in data:
            data["evidence"] = to_string_tuple(data["evidence"])
        return cls(**data)


__all__ = ["Belief"]
