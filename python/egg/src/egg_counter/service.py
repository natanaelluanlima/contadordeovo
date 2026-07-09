from __future__ import annotations

import base64
import logging
from collections import deque
from dataclasses import dataclass
from time import perf_counter, time
from typing import Any

import cv2
import numpy as np

from egg_counter.config import (
    CameraConfig,
    RuntimeConfig,
    detect_video_profile,
    load_named_video_profile,
)
from egg_counter.counting import LineCounter
from egg_counter.detection import Detector
from egg_counter.models import CountEvent, TrackedDetection
from egg_counter.pipeline import (
    VideoSource,
    detect_center_divider_zone,
    filter_excluded_detections,
    preprocess_frame,
    scaled_geometry,
)
from egg_counter.tracking import CentroidTracker

logger = logging.getLogger(__name__)

_FPS_WINDOW = 10
_PREVIEW_SCALE = 0.55
_PREVIEW_JPEG_QUALITY = 55


@dataclass(slots=True)
class FramePipelineResult:
    tracked_objects: list[TrackedDetection]
    events: list[CountEvent]


class EggCounterService:
    def __init__(self, camera: CameraConfig, runtime: RuntimeConfig) -> None:
        self.camera = camera
        self.runtime = runtime
        self.detector = Detector(runtime)
        self.tracker = CentroidTracker(
            max_distance=runtime.match_distance,
            max_missing=runtime.max_missing,
        )
        self.counter = LineCounter(camera.line)
        self._last_fps = 0.0
        self._frame_durations: deque[float] = deque(maxlen=_FPS_WINDOW)
        self._last_updated_at = time()
        self._last_event: CountEvent | None = None
        self._last_events: list[CountEvent] = []
        self._last_annotated_frame_b64: str | None = None
        self._last_roi = camera.roi
        self._last_line = camera.line
        self._profile_locked = False
        self._geometry_cache: tuple[tuple[int, int], tuple[Any, Any, list[Any]]] | None = None
        self._divider_zone_cache = None

    def configure_for_frame(self, frame: np.ndarray) -> None:
        height, width = frame.shape[:2]
        profile = detect_video_profile(width, height)
        if profile is None:
            self._profile_locked = True
            return

        camera, runtime = load_named_video_profile(profile)
        self.reconfigure(camera, runtime)
        self._profile_locked = True
        logger.info("Perfil de video selecionado automaticamente: %s (%sx%s)", profile, width, height)

    def reconfigure(self, camera: CameraConfig, runtime: RuntimeConfig) -> None:
        self.camera = camera
        self.runtime = runtime
        self.detector = Detector(runtime)
        self.reset()

    def reset(self) -> None:
        self.tracker = CentroidTracker(
            max_distance=self.runtime.match_distance,
            max_missing=self.runtime.max_missing,
        )
        self.counter = LineCounter(self.camera.line)
        self._last_fps = 0.0
        self._frame_durations.clear()
        self._last_updated_at = time()
        self._last_event = None
        self._last_events = []
        self._last_annotated_frame_b64 = None
        self._last_roi = self.camera.roi
        self._last_line = self.camera.line
        self._geometry_cache = None
        self._divider_zone_cache = None

    def process_frame(self, frame: np.ndarray) -> dict[str, Any]:
        if not self._profile_locked:
            self.configure_for_frame(frame)

        started_at = perf_counter()
        result = self._run_pipeline(frame)
        self._update_fps(started_at)

        debug_frame = self._draw_debug_frame(
            frame,
            result.tracked_objects,
            result.events,
            preview_scale=_PREVIEW_SCALE,
        )
        self._last_annotated_frame_b64 = _encode_frame_b64(debug_frame, quality=_PREVIEW_JPEG_QUALITY)
        return self._build_frame_result(result.events)

    def process_stream(self, max_frames: int | None = None, display: bool = True) -> None:
        processed_frames = 0
        with VideoSource(self.camera) as video_source:
            while True:
                started_at = perf_counter()
                frame = video_source.read()
                if frame is None:
                    logger.info("Fim da fonte de video ou falha na leitura.")
                    break

                result = self._run_pipeline(frame)
                self._update_fps(started_at)

                if display and self.camera.show_window:
                    debug_frame = self._draw_debug_frame(frame, result.tracked_objects, result.events)
                    cv2.imshow("Egg Counter", debug_frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

                processed_frames += 1
                if max_frames is not None and processed_frames >= max_frames:
                    break

        cv2.destroyAllWindows()

    def _run_pipeline(self, frame: np.ndarray) -> FramePipelineResult:
        height, width = frame.shape[:2]
        size_key = (height, width)

        if self._geometry_cache is not None and self._geometry_cache[0] == size_key:
            roi, line, exclude_zones = self._geometry_cache[1]
        else:
            roi, line, exclude_zones = scaled_geometry(
                frame,
                self.camera.width,
                self.camera.height,
                self.camera.roi,
                self.camera.line,
                self.camera.exclude_zones,
            )
            if self._divider_zone_cache is None:
                self._divider_zone_cache = detect_center_divider_zone(frame)
            if self._divider_zone_cache is not None:
                exclude_zones = [*exclude_zones, self._divider_zone_cache]
            if self._profile_locked:
                self._geometry_cache = (size_key, (roi, line, exclude_zones))

        self.counter.line = line

        prepared = preprocess_frame(
            frame,
            roi,
            normalize=self.runtime.normalize,
            crop_roi=self.camera.crop_roi,
        )
        detections = self.detector.detect(prepared.frame, offset=prepared.offset)
        detections = filter_excluded_detections(detections, exclude_zones)
        tracked_objects = self.tracker.update(detections)
        events = self.counter.update(tracked_objects)
        if events:
            self._last_event = events[-1]
        self._last_events = events
        self._last_roi = roi
        self._last_line = line
        return FramePipelineResult(tracked_objects=tracked_objects, events=events)

    def _update_fps(self, started_at: float) -> None:
        elapsed = perf_counter() - started_at
        if elapsed > 0:
            self._frame_durations.append(elapsed)
            average_duration = sum(self._frame_durations) / len(self._frame_durations)
            self._last_fps = 1.0 / average_duration
        self._last_updated_at = time()

    @property
    def last_annotated_frame_b64(self) -> str | None:
        return self._last_annotated_frame_b64

    def snapshot_status(self) -> dict[str, Any]:
        return {
            "total_count": self.counter.total_count,
            "active_tracks": self.tracker.active_track_count,
            "fps": round(self._last_fps, 2),
            "backend": self.runtime.backend,
            "model_path": self.runtime.model_path,
            "last_updated_at": self._last_updated_at,
            "last_event": None
            if self._last_event is None
            else {
                "track_id": self._last_event.track_id,
                "label": self._last_event.label,
                "total_count": self._last_event.total_count,
                "timestamp": self._last_event.timestamp,
            },
            "events": [_serialize_event(event) for event in self._last_events],
        }

    def _build_frame_result(self, events: list[CountEvent]) -> dict[str, Any]:
        return {
            "total_count": self.counter.total_count,
            "active_tracks": self.tracker.active_track_count,
            "fps": round(self._last_fps, 2),
            "annotated_frame_b64": self._last_annotated_frame_b64,
            "events": [_serialize_event(event) for event in events],
        }

    def _draw_debug_frame(
        self,
        frame,
        tracked_objects: list[TrackedDetection],
        events: list[CountEvent],
        preview_scale: float = 1.0,
    ):
        if preview_scale != 1.0:
            height, width = frame.shape[:2]
            scaled_width = max(1, int(width * preview_scale))
            scaled_height = max(1, int(height * preview_scale))
            overlay = cv2.resize(
                frame,
                (scaled_width, scaled_height),
                interpolation=cv2.INTER_AREA,
            )
        else:
            overlay = frame.copy()
            preview_scale = 1.0

        roi_color = (255, 128, 0)
        line_color = (255, 128, 0)
        egg_color = (0, 0, 255)

        if self._last_roi.width > 0 and self._last_roi.height > 0:
            x = int(self._last_roi.x * preview_scale)
            y = int(self._last_roi.y * preview_scale)
            w = int(self._last_roi.width * preview_scale)
            h = int(self._last_roi.height * preview_scale)
            cv2.rectangle(overlay, (x, y), (x + w, y + h), roi_color, 2)

        cv2.line(
            overlay,
            (int(self._last_line.x1 * preview_scale), int(self._last_line.y1 * preview_scale)),
            (int(self._last_line.x2 * preview_scale), int(self._last_line.y2 * preview_scale)),
            line_color,
            2,
        )

        for tracked in tracked_objects:
            if tracked.label != "egg":
                continue

            x1, y1, x2, y2 = tracked.bbox
            cv2.rectangle(
                overlay,
                (int(x1 * preview_scale), int(y1 * preview_scale)),
                (int(x2 * preview_scale), int(y2 * preview_scale)),
                egg_color,
                2,
            )

        total_text = f"TOTAL: {self.counter.total_count}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.9
        thickness = 2
        (text_width, text_height), _ = cv2.getTextSize(total_text, font, scale, thickness)
        text_x = max(10, overlay.shape[1] - text_width - 20)
        text_y = text_height + 16
        cv2.putText(
            overlay,
            total_text,
            (text_x, text_y),
            font,
            scale,
            (255, 255, 255),
            thickness + 2,
            cv2.LINE_AA,
        )
        cv2.putText(
            overlay,
            total_text,
            (text_x, text_y),
            font,
            scale,
            roi_color,
            thickness,
            cv2.LINE_AA,
        )

        if events:
            event = events[-1]
            event_text = f"+1 ID {event.track_id}"
            cv2.putText(
                overlay,
                event_text,
                (20, overlay.shape[0] - 20),
                font,
                0.7,
                egg_color,
                2,
                cv2.LINE_AA,
            )

        return overlay


def _serialize_event(event: CountEvent) -> dict[str, Any]:
    return {
        "track_id": event.track_id,
        "label": event.label,
        "total_count": event.total_count,
        "timestamp": event.timestamp,
    }


def _encode_frame_b64(frame: np.ndarray, quality: int = 75) -> str:
    ok, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise RuntimeError("Falha ao codificar frame para JPEG.")
    return base64.b64encode(buffer).decode("ascii")
