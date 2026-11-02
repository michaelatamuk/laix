"""Perception records: detectors, detections and frames.

The records are part of the decision vocabulary. The host supplies detectors
and drives the clock; the runtime loop lives in ``laix.appkit.live_context``.
"""

from __future__ import annotations

from .detection import Detection
from .detector import Detector
from .event import PerceptionEvent
from .frame import PerceptionFrame

__all__ = ["Detection", "Detector", "PerceptionEvent", "PerceptionFrame"]
