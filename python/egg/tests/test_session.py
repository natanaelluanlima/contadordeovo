import cv2
import numpy as np
import pytest

from egg_counter.config import CameraConfig, LineConfig, RuntimeConfig
from egg_counter.session import ProcessadorSession


def _jpeg_bytes(frame: np.ndarray) -> bytes:
    ok, buffer = cv2.imencode(".jpg", frame)
    assert ok
    return buffer.tobytes()


def test_status_returns_last_events_after_frame() -> None:
    session = ProcessadorSession(
        camera=CameraConfig(line=LineConfig(x1=0, y1=100, x2=200, y2=100, direction="bottom_to_top")),
        runtime=RuntimeConfig(backend="classic", normalize=False, reference_image=None),
    )
    session.start({"mode": "browser_camera"})

    frame = np.zeros((200, 200, 3), dtype=np.uint8)
    session.process_frame_bytes(_jpeg_bytes(frame))

    status = session.status()
    assert status["state"] == "running"
    assert status["mode"] == "browser_camera"
    assert "events" in status
    assert isinstance(status["events"], list)


def test_process_frame_without_start_raises() -> None:
    session = ProcessadorSession(
        camera=CameraConfig(),
        runtime=RuntimeConfig(backend="classic", normalize=False, reference_image=None),
    )
    frame = np.zeros((64, 64, 3), dtype=np.uint8)

    with pytest.raises(RuntimeError, match="sessao ativa"):
        session.process_frame_bytes(_jpeg_bytes(frame))
