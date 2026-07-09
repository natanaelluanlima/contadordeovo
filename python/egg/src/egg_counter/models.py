from __future__ import annotations

from dataclasses import dataclass, field
from time import time


@dataclass(slots=True)
class Detection:
    bbox: tuple[int, int, int, int]
    confidence: float
    label: str

    @property
    def center(self) -> tuple[int, int]:
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)


@dataclass(slots=True)
class TrackedDetection(Detection):
    track_id: int
    previous_center: tuple[int, int] | None = None


@dataclass(slots=True)
class CountEvent:
    track_id: int
    label: str
    total_count: int
    timestamp: float = field(default_factory=time)
