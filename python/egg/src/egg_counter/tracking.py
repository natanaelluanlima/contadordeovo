from __future__ import annotations

from dataclasses import dataclass
from math import dist

from egg_counter.models import Detection, TrackedDetection


@dataclass(slots=True)
class TrackState:
    track_id: int
    bbox: tuple[int, int, int, int]
    center: tuple[int, int]
    previous_center: tuple[int, int] | None
    label: str
    confidence: float
    missing_frames: int = 0
    hits: int = 1
    velocity: tuple[float, float] = (0.0, 0.0)


class CentroidTracker:
    """Centroid tracker that coasts confirmed tracks across missed detections."""

    def __init__(
        self,
        max_distance: float = 90.0,
        max_missing: int = 12,
        min_hits: int = 1,
    ) -> None:
        self.max_distance = max_distance
        self.max_missing = max_missing
        self.min_hits = min_hits
        self._next_track_id = 1
        self._tracks: dict[int, TrackState] = {}

    def update(self, detections: list[Detection]) -> list[TrackedDetection]:
        if not self._tracks and not detections:
            return []

        if not self._tracks:
            return [self._register(detection) for detection in detections]

        assigned_tracks: set[int] = set()
        assigned_detections: set[int] = set()
        candidates: list[tuple[float, int, int]] = []
        tracked_detections: list[TrackedDetection] = []

        if detections:
            for track_id, track in self._tracks.items():
                for index, detection in enumerate(detections):
                    candidates.append((dist(track.center, detection.center), track_id, index))

            candidates.sort(key=lambda item: item[0])

            for distance, track_id, detection_index in candidates:
                if track_id in assigned_tracks or detection_index in assigned_detections:
                    continue

                detection = detections[detection_index]
                track = self._tracks[track_id]
                overlap = _bbox_iou(track.bbox, detection.bbox)
                max_distance = self.max_distance * 2.4 if overlap >= 0.08 else self.max_distance
                if distance > max_distance:
                    continue

                previous_center = track.center
                vx = float(detection.center[0] - previous_center[0])
                vy = float(detection.center[1] - previous_center[1])
                track.velocity = (
                    0.7 * vx + 0.3 * track.velocity[0],
                    0.7 * vy + 0.3 * track.velocity[1],
                )
                # Snap to detection for exact follow (no laggy blend)
                track.bbox = detection.bbox
                track.center = detection.center
                track.previous_center = previous_center
                track.label = detection.label
                track.confidence = detection.confidence
                track.missing_frames = 0
                track.hits += 1

                assigned_tracks.add(track_id)
                assigned_detections.add(detection_index)
                tracked_detections.append(
                    TrackedDetection(
                        bbox=track.bbox,
                        confidence=track.confidence,
                        label=detection.label,
                        track_id=track_id,
                        previous_center=previous_center,
                    )
                )

            for detection_index, detection in enumerate(detections):
                if detection_index in assigned_detections:
                    continue
                tracked_detections.append(self._register(detection))

        # Coast only when motion is reliable — avoids ghost boxes drifting on empty belt
        for track_id, track in list(self._tracks.items()):
            if track_id in assigned_tracks:
                continue
            track.missing_frames += 1
            if track.hits < self.min_hits:
                self._tracks.pop(track_id, None)
                continue
            if track.missing_frames > self.max_missing:
                self._tracks.pop(track_id, None)
                continue

            speed = (track.velocity[0] ** 2 + track.velocity[1] ** 2) ** 0.5
            if speed < 1.5 and track.missing_frames >= 3:
                # Unreliable coast — drop instead of leaving a ghost box
                self._tracks.pop(track_id, None)
                continue

            predicted = self._predict_bbox(track)
            track.previous_center = track.center
            track.bbox = predicted
            track.center = (
                (predicted[0] + predicted[2]) // 2,
                (predicted[1] + predicted[3]) // 2,
            )
            track.confidence = max(0.30, track.confidence * 0.96)
            tracked_detections.append(
                TrackedDetection(
                    bbox=track.bbox,
                    confidence=track.confidence,
                    label=track.label,
                    track_id=track.track_id,
                    previous_center=track.previous_center,
                )
            )

        return tracked_detections

    @property
    def active_track_count(self) -> int:
        return len(self._tracks)

    def drop_track(self, track_id: int) -> None:
        self._tracks.pop(track_id, None)

    def _predict_bbox(self, track: TrackState) -> tuple[int, int, int, int]:
        x1, y1, x2, y2 = track.bbox
        dx = int(round(track.velocity[0]))
        dy = int(round(track.velocity[1]))
        # Prefer upward coast for bottom_to_top belts when velocity is unknown
        if dx == 0 and dy == 0:
            dy = -2
        width = max(1, x2 - x1)
        height = max(1, y2 - y1)
        nx1 = x1 + dx
        ny1 = y1 + dy
        return (nx1, ny1, nx1 + width, ny1 + height)

    def _register(self, detection: Detection) -> TrackedDetection:
        track_id = self._next_track_id
        self._next_track_id += 1

        self._tracks[track_id] = TrackState(
            track_id=track_id,
            bbox=detection.bbox,
            center=detection.center,
            previous_center=None,
            label=detection.label,
            confidence=detection.confidence,
            hits=1,
        )

        return TrackedDetection(
            bbox=detection.bbox,
            confidence=detection.confidence,
            label=detection.label,
            track_id=track_id,
            previous_center=None,
        )


def _blend_bbox(
    previous: tuple[int, int, int, int],
    current: tuple[int, int, int, int],
    alpha: float = 0.65,
) -> tuple[int, int, int, int]:
    """Blend boxes to keep overlays stable across frames."""
    beta = 1.0 - alpha
    return (
        int(round(alpha * current[0] + beta * previous[0])),
        int(round(alpha * current[1] + beta * previous[1])),
        int(round(alpha * current[2] + beta * previous[2])),
        int(round(alpha * current[3] + beta * previous[3])),
    )


def _bbox_iou(
    box_a: tuple[int, int, int, int],
    box_b: tuple[int, int, int, int],
) -> float:
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
        return 0.0

    intersection = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    union = area_a + area_b - intersection
    if union <= 0:
        return 0.0
    return intersection / union
