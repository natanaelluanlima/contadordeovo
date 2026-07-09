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


class CentroidTracker:
    def __init__(self, max_distance: float = 90.0, max_missing: int = 12) -> None:
        self.max_distance = max_distance
        self.max_missing = max_missing
        self._next_track_id = 1
        self._tracks: dict[int, TrackState] = {}

    def update(self, detections: list[Detection]) -> list[TrackedDetection]:
        if not detections:
            self._mark_missing()
            return []

        if not self._tracks:
            return [self._register(detection) for detection in detections]

        assigned_tracks: set[int] = set()
        assigned_detections: set[int] = set()
        candidates: list[tuple[float, int, int]] = []

        for track_id, track in self._tracks.items():
            for index, detection in enumerate(detections):
                candidates.append((dist(track.center, detection.center), track_id, index))

        candidates.sort(key=lambda item: item[0])
        tracked_detections: list[TrackedDetection] = []

        for distance, track_id, detection_index in candidates:
            if track_id in assigned_tracks or detection_index in assigned_detections:
                continue

            detection = detections[detection_index]
            track = self._tracks[track_id]
            overlap = _bbox_iou(track.bbox, detection.bbox)
            max_distance = self.max_distance * 2 if overlap >= 0.15 else self.max_distance
            if distance > max_distance:
                continue
            previous_center = track.center
            track.bbox = detection.bbox
            track.center = detection.center
            track.previous_center = previous_center
            track.label = detection.label
            track.confidence = detection.confidence
            track.missing_frames = 0

            assigned_tracks.add(track_id)
            assigned_detections.add(detection_index)
            tracked_detections.append(
                TrackedDetection(
                    bbox=detection.bbox,
                    confidence=detection.confidence,
                    label=detection.label,
                    track_id=track_id,
                    previous_center=previous_center,
                )
            )

        for detection_index, detection in enumerate(detections):
            if detection_index in assigned_detections:
                continue
            tracked_detections.append(self._register(detection))

        self._mark_missing(except_ids=assigned_tracks)
        return tracked_detections

    @property
    def active_track_count(self) -> int:
        return len(self._tracks)

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
        )

        return TrackedDetection(
            bbox=detection.bbox,
            confidence=detection.confidence,
            label=detection.label,
            track_id=track_id,
            previous_center=None,
        )

    def _mark_missing(self, except_ids: set[int] | None = None) -> None:
        protected = except_ids or set()
        to_remove: list[int] = []

        for track_id, track in self._tracks.items():
            if track_id in protected:
                continue

            track.missing_frames += 1
            if track.missing_frames > self.max_missing:
                to_remove.append(track_id)

        for track_id in to_remove:
            self._tracks.pop(track_id, None)


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
