import numpy as np

from egg_counter.config import RoiConfig
from egg_counter.models import Detection
from egg_counter.pipeline import (
    _point_in_zone,
    detect_center_divider_zone,
    filter_excluded_detections,
)


def test_point_in_zone() -> None:
    zone = RoiConfig(x=10, y=20, width=30, height=40)
    assert _point_in_zone(25, 35, zone)
    assert not _point_in_zone(5, 35, zone)


def test_filter_excluded_detections() -> None:
    zone = RoiConfig(x=0, y=0, width=100, height=100)
    detections = [
        Detection(bbox=(10, 10, 30, 30), confidence=0.9, label="egg"),
        Detection(bbox=(120, 60, 140, 80), confidence=0.9, label="egg"),
    ]

    kept = filter_excluded_detections(detections, [zone])

    assert len(kept) == 1
    assert kept[0].bbox[0] == 120


def test_detect_center_divider_zone_on_dual_lane_frame() -> None:
    frame = np.full((540, 960, 3), 220, dtype=np.uint8)
    frame[:, 410:550] = 70

    zone = detect_center_divider_zone(frame)

    assert zone is not None
    assert zone.x >= 300
    assert zone.x + zone.width <= 700


def test_detect_center_divider_zone_ignores_single_lane_frame() -> None:
    frame = np.full((478, 848, 3), 180, dtype=np.uint8)
    frame[:, 250:] = 225

    assert detect_center_divider_zone(frame) is None
