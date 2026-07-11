from __future__ import annotations

from math import dist

from egg_counter.config import LineConfig
from egg_counter.models import CountEvent, TrackedDetection


class LineCounter:
    """Counts eggs once when they cross the line in the configured direction."""

    def __init__(self, line: LineConfig, *, spatial_cooldown_px: float = 38.0) -> None:
        self.line = line
        self.total_count = 0
        self.counted_track_ids: set[int] = set()
        self.spatial_cooldown_px = spatial_cooldown_px
        self._recent_crossings: list[tuple[float, float]] = []

    def update(self, tracked_objects: list[TrackedDetection]) -> list[CountEvent]:
        events: list[CountEvent] = []
        for tracked in tracked_objects:
            if tracked.track_id in self.counted_track_ids:
                continue
            # Require a real previous center — synthetic late detections caused overcount
            previous_center = tracked.previous_center
            if previous_center is None:
                continue
            if not self._crossed_line(previous_center, tracked.center):
                continue
            if not self._matches_direction(previous_center, tracked.center):
                continue
            if self._is_near_recent_crossing(tracked.center):
                # Same physical egg re-registered with a new track id
                self.counted_track_ids.add(tracked.track_id)
                continue

            self.total_count += 1
            self.counted_track_ids.add(tracked.track_id)
            self._recent_crossings.append((float(tracked.center[0]), float(tracked.center[1])))
            if len(self._recent_crossings) > 40:
                self._recent_crossings = self._recent_crossings[-40:]
            events.append(
                CountEvent(
                    track_id=tracked.track_id,
                    label=tracked.label,
                    total_count=self.total_count,
                )
            )
        return events

    def _is_near_recent_crossing(self, center: tuple[int, int]) -> bool:
        for previous in self._recent_crossings:
            if dist(center, previous) <= self.spatial_cooldown_px:
                return True
        return False

    def _crossed_line(
        self,
        previous_center: tuple[int, int],
        current_center: tuple[int, int],
    ) -> bool:
        if previous_center == current_center:
            return False

        previous_side = self._signed_side(previous_center)
        current_side = self._signed_side(current_center)
        if previous_side != 0 and current_side != 0:
            return (previous_side < 0 < current_side) or (previous_side > 0 > current_side)

        return _segments_intersect(
            previous_center,
            current_center,
            (self.line.x1, self.line.y1),
            (self.line.x2, self.line.y2),
        )

    def _matches_direction(
        self,
        previous_center: tuple[int, int],
        current_center: tuple[int, int],
    ) -> bool:
        delta_x = current_center[0] - previous_center[0]
        delta_y = current_center[1] - previous_center[1]

        direction = self.line.direction
        if direction == "top_to_bottom":
            return delta_y > 0
        if direction == "bottom_to_top":
            return delta_y < 0
        if direction == "left_to_right":
            return delta_x > 0
        if direction == "right_to_left":
            return delta_x < 0
        return True

    def _signed_side(self, point: tuple[int, int]) -> int:
        x1, y1, x2, y2 = self.line.x1, self.line.y1, self.line.x2, self.line.y2
        x, y = point
        return int((x - x1) * (y2 - y1) - (y - y1) * (x2 - x1))


def _segments_intersect(
    a1: tuple[int, int],
    a2: tuple[int, int],
    b1: tuple[int, int],
    b2: tuple[int, int],
) -> bool:
    def orientation(p: tuple[int, int], q: tuple[int, int], r: tuple[int, int]) -> int:
        value = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
        if value == 0:
            return 0
        return 1 if value > 0 else 2

    def on_segment(p: tuple[int, int], q: tuple[int, int], r: tuple[int, int]) -> bool:
        return (
            min(p[0], r[0]) <= q[0] <= max(p[0], r[0])
            and min(p[1], r[1]) <= q[1] <= max(p[1], r[1])
        )

    o1 = orientation(a1, a2, b1)
    o2 = orientation(a1, a2, b2)
    o3 = orientation(b1, b2, a1)
    o4 = orientation(b1, b2, a2)

    if o1 != o2 and o3 != o4:
        return True

    if o1 == 0 and on_segment(a1, b1, a2):
        return True
    if o2 == 0 and on_segment(a1, b2, a2):
        return True
    if o3 == 0 and on_segment(b1, a1, b2):
        return True
    if o4 == 0 and on_segment(b1, a2, b2):
        return True

    return False
