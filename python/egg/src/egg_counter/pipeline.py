from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from egg_counter.config import CameraConfig, LineConfig, RoiConfig


@dataclass(slots=True)
class ProcessedFrame:
    frame: np.ndarray
    offset: tuple[int, int]


class VideoSource:
    def __init__(self, config: CameraConfig) -> None:
        self.config = config
        self.capture: cv2.VideoCapture | None = None

    def __enter__(self) -> "VideoSource":
        self.open()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def open(self) -> None:
        self.capture = cv2.VideoCapture(self.config.source)
        if not self.capture.isOpened():
            raise RuntimeError(f"Nao foi possivel abrir a fonte de video: {self.config.source}")

        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
        self.capture.set(cv2.CAP_PROP_FPS, self.config.fps)

    def read(self) -> np.ndarray | None:
        if self.capture is None:
            raise RuntimeError("A fonte de video ainda nao foi aberta.")

        ok, frame = self.capture.read()
        if not ok:
            return None
        return frame

    def close(self) -> None:
        if self.capture is not None:
            self.capture.release()
            self.capture = None


def preprocess_frame(
    frame: np.ndarray,
    roi: RoiConfig,
    normalize: bool = True,
    crop_roi: bool = True,
) -> ProcessedFrame:
    cropped, offset = crop_to_roi(frame, roi) if crop_roi else (frame, (0, 0))
    if normalize:
        cropped = normalize_lighting(cropped)
    return ProcessedFrame(frame=cropped, offset=offset)


def scale_roi(roi: RoiConfig, sx: float, sy: float) -> RoiConfig:
    return RoiConfig(
        x=int(roi.x * sx),
        y=int(roi.y * sy),
        width=int(roi.width * sx),
        height=int(roi.height * sy),
    )


def scale_line(line: LineConfig, sx: float, sy: float) -> LineConfig:
    return LineConfig(
        x1=int(line.x1 * sx),
        y1=int(line.y1 * sy),
        x2=int(line.x2 * sx),
        y2=int(line.y2 * sy),
        direction=line.direction,
    )


def scaled_geometry(
    frame: np.ndarray,
    reference_width: int,
    reference_height: int,
    roi: RoiConfig,
    line: LineConfig,
    exclude_zones: list[RoiConfig] | None = None,
) -> tuple[RoiConfig, LineConfig, list[RoiConfig]]:
    frame_height, frame_width = frame.shape[:2]
    zones = exclude_zones or []
    if reference_width <= 0 or reference_height <= 0:
        return roi, line, zones
    if frame_width == reference_width and frame_height == reference_height:
        return roi, line, zones

    sx = frame_width / reference_width
    sy = frame_height / reference_height
    scaled_zones = [scale_roi(zone, sx, sy) for zone in zones]
    return scale_roi(roi, sx, sy), scale_line(line, sx, sy), scaled_zones


def detect_center_divider_zone(frame: np.ndarray) -> RoiConfig | None:
    height, width = frame.shape[:2]
    if width < 900:
        # So aplica em esteira dupla larga (ex.: VIDEO PADRAO 960x540)
        return None

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    band_width = max(40, width // 12)
    center_x = width // 2
    x1 = max(0, center_x - band_width // 2)
    x2 = min(width, center_x + band_width // 2)
    center_band = gray[:, x1:x2]
    side_width = max(40, width // 5)
    left_band = gray[:, max(0, center_x - side_width - band_width) : max(0, center_x - band_width)]
    right_band = gray[:, min(width, center_x + band_width) : min(width, center_x + band_width + side_width)]
    if left_band.size == 0 or right_band.size == 0:
        return None

    belt_brightness = max(float(left_band.mean()), float(right_band.mean()))
    center_brightness = float(center_band.mean())
    if belt_brightness - center_brightness < 45:
        return None

    exclude_width = max(band_width * 2, width // 6)
    exclude_x = max(0, center_x - exclude_width // 2)
    return RoiConfig(x=exclude_x, y=0, width=min(exclude_width, width - exclude_x), height=height)


def filter_excluded_detections(
    detections: list,
    exclude_zones: list[RoiConfig],
) -> list:
    if not exclude_zones:
        return detections

    kept = []
    for detection in detections:
        center_x = (detection.bbox[0] + detection.bbox[2]) // 2
        center_y = (detection.bbox[1] + detection.bbox[3]) // 2
        if any(_point_in_zone(center_x, center_y, zone) for zone in exclude_zones):
            continue
        kept.append(detection)
    return kept


def _point_in_zone(x: int, y: int, zone: RoiConfig) -> bool:
    if zone.width <= 0 or zone.height <= 0:
        return False
    return zone.x <= x <= zone.x + zone.width and zone.y <= y <= zone.y + zone.height


def crop_to_roi(frame: np.ndarray, roi: RoiConfig) -> tuple[np.ndarray, tuple[int, int]]:
    if roi.width <= 0 or roi.height <= 0:
        return frame, (0, 0)

    x1 = max(roi.x, 0)
    y1 = max(roi.y, 0)
    x2 = min(x1 + roi.width, frame.shape[1])
    y2 = min(y1 + roi.height, frame.shape[0])
    return frame[y1:y2, x1:x2], (x1, y1)


def normalize_lighting(frame: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_l = clahe.apply(l_channel)
    merged = cv2.merge((enhanced_l, a_channel, b_channel))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
