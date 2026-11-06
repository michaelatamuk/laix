"""External comparison package."""

from .adapters.langgraph.adapter import LangGraphAdapter
from .adapters.protocol import ExternalAdapter
from .adapters.result import AdapterResult
from .adapters.temporal.adapter import TemporalAdapter

__all__ = ["AdapterResult", "ExternalAdapter", "LangGraphAdapter", "TemporalAdapter"]
