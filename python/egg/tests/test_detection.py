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
    bbox = (80, 40, 130, 90)

    assert backend._is_on_irregular_belt(frame, bbox, 12.0)


def test_accepts_solid_brown_egg_blob() -> None:
    backend = _backend()
    frame = np.full((200, 200, 3), 235, dtype=np.uint8)
    cv2.ellipse(frame, (100, 100), (28, 20), 0, 0, 360, (120, 150, 190), -1)

    assert backend._is_filled_egg_blob(frame, (72, 80, 128, 120), 12.0)


def test_rejects_ring_like_artifact() -> None:
    backend = _backend()
    frame = np.full((200, 200, 3), 235, dtype=np.uint8)
    cv2.ellipse(frame, (100, 100), (28, 20), 0, 0, 360, (120, 150, 190), 3)

    assert not backend._is_filled_egg_blob(frame, (72, 80, 128, 120), 12.0)


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
