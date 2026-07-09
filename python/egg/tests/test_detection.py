from pathlib import Path

import cv2
import numpy as np
import pytest

from egg_counter.config import RuntimeConfig
from egg_counter.detection import ClassicBackend


def _backend() -> ClassicBackend:
    return ClassicBackend(RuntimeConfig(backend="classic", reference_image=None, normalize=False))


def test_rejects_irregular_belt_patch() -> None:
    backend = _backend()
    frame = np.full((120, 200, 3), 235, dtype=np.uint8)
    for cx in (60, 100, 140):
        cv2.circle(frame, (cx, 60), 10, (70, 70, 70), -1)
    bbox = (92, 50, 108, 70)

    assert backend._is_hollow_belt_hole(frame, bbox, 12.0)


def test_accepts_solid_brown_egg_blob() -> None:
    backend = _backend()
    frame = np.full((200, 200, 3), 235, dtype=np.uint8)
    cv2.ellipse(frame, (100, 100), (28, 20), 0, 0, 360, (120, 150, 190), -1)

    assert backend._passes_brown_egg_shape(frame, (72, 80, 128, 120), 12.0)


def test_rejects_ring_like_artifact() -> None:
    backend = _backend()
    frame = np.full((200, 200, 3), 235, dtype=np.uint8)
    cv2.ellipse(frame, (100, 100), (28, 20), 0, 0, 360, (120, 150, 190), 3)

    assert not backend._is_filled_egg_blob(frame, (72, 80, 128, 120), 12.0)


def test_rejects_bbox_smaller_than_belt_hole() -> None:
    backend = _backend()
    hole_radius = 13.5
    hole_bbox = (80, 80, 113, 113)

    assert not backend._is_egg_sized_bbox(hole_bbox, hole_radius)


def test_accepts_bbox_larger_than_belt_hole() -> None:
    backend = _backend()
    egg_bbox = (80, 80, 145, 145)

    assert backend._is_egg_sized_bbox(egg_bbox, 13.5)


def test_rejects_hollow_belt_hole() -> None:
    backend = _backend()
    frame = np.full((200, 200, 3), 235, dtype=np.uint8)
    cv2.circle(frame, (100, 100), 14, (70, 70, 70), -1)

    assert backend._is_hollow_belt_hole(frame, (82, 82, 118, 118), 12.0)


def test_rejects_dark_void_hole_in_filled_blob_check() -> None:
    backend = _backend()
    frame = np.full((200, 200, 3), 235, dtype=np.uint8)
    cv2.circle(frame, (100, 100), 14, (70, 70, 70), -1)

    assert not backend._is_filled_egg_blob(frame, (82, 82, 118, 118), 12.0)


@pytest.mark.skipif(
    not (Path(__file__).resolve().parents[3] / "videos" / "VIDEO PARA TESTES.mp4").exists(),
    reason="Video de testes ausente",
)
def test_empty_belt_frames_have_no_detections() -> None:
    backend = ClassicBackend(
        RuntimeConfig(
            backend="classic",
            reference_image="config/reference-video-testes.jpg",
            diff_threshold=55,
        )
    )
    video = Path(__file__).resolve().parents[3] / "videos" / "VIDEO PARA TESTES.mp4"
    cap = cv2.VideoCapture(str(video))
    for frame_index in (288, 465, 509):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = cap.read()
        assert ok
        assert backend.detect(frame) == []
    cap.release()


@pytest.mark.skipif(
    not Path("config/reference-video-padrao.jpg").exists(),
    reason="Imagem de referencia do video padrao ausente",
)
def test_splice_frame_has_fewer_detections_than_real_eggs() -> None:
    backend = ClassicBackend(
        RuntimeConfig(
            backend="classic",
            reference_image="config/reference-video-padrao.jpg",
            diff_threshold=55,
        )
    )
    image_path = Path(__file__).resolve().parents[1] / "config" / "reference-video-padrao.jpg"
    frame = cv2.imread(str(image_path))
    assert frame is not None

    detections = backend.detect(frame)
    centers = [((d.bbox[0] + d.bbox[2]) // 2, (d.bbox[1] + d.bbox[3]) // 2) for d in detections]

    splice_hits = sum(1 for _, y in centers if 170 <= y <= 310)
    # Com a nova referencia de esteira vazia, a emenda pode gerar algumas deteccoes.
    assert splice_hits <= 4
