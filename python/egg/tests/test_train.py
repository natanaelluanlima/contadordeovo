from __future__ import annotations

from egg_counter.train import bbox_to_yolo


def test_bbox_to_yolo_normalizes_center_and_size() -> None:
    xc, yc, bw, bh = bbox_to_yolo((100, 50, 200, 150), width=400, height=200)
    assert abs(xc - 0.375) < 1e-6
    assert abs(yc - 0.5) < 1e-6
    assert abs(bw - 0.25) < 1e-6
    assert abs(bh - 0.5) < 1e-6
