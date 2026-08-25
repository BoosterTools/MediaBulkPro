"""Event types emitted by the QueueManager so UI layers can react without
the manager itself depending on Qt."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class QueueEvent:
    type: str          # "added" | "status_changed" | "progress" | "removed" | "reordered"
    item_id: int
    data: dict[str, Any]
