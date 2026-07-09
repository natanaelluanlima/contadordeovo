from __future__ import annotations

import base64
import logging
from threading import Lock
from typing import Any

import cv2
import numpy as np

from egg_counter.config import CameraConfig, RuntimeConfig
from egg_counter.service import EggCounterService

logger = logging.getLogger(__name__)


class ProcessadorSession:
    def __init__(self, camera: CameraConfig, runtime: RuntimeConfig) -> None:
        self._camera = camera
        self._runtime = runtime
        self._lock = Lock()
        self._service = EggCounterService(camera=camera, runtime=runtime)
        self._state = "idle"
        self._mode = "none"

    def status(self) -> dict[str, Any]:
        with self._lock:
            return self._build_status()

    def start(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._lock:
            payload = body or {}
            self._mode = str(payload.get("mode", "browser_camera"))
            self._service.reset()
            self._service._profile_locked = False
            self._state = "running"
            logger.info("Sessao iniciada no modo %s", self._mode)
            return self._build_status()

    def stop(self) -> dict[str, Any]:
        with self._lock:
            self._state = "idle"
            self._mode = "none"
            logger.info("Sessao encerrada")
            return self._build_status()

    def process_frame_bytes(self, frame_bytes: bytes) -> dict[str, Any]:
        frame = _decode_frame(frame_bytes)
        return self._process_frame(frame)

    def process_frame_b64(self, image_b64: str) -> dict[str, Any]:
        frame_bytes = base64.b64decode(image_b64)
        return self.process_frame_bytes(frame_bytes)

    def _process_frame(self, frame: np.ndarray) -> dict[str, Any]:
        with self._lock:
            if self._state != "running":
                raise RuntimeError("Nenhuma sessao ativa. Chame /v1/session/start antes de enviar frames.")

            result = self._service.process_frame(frame)
            return {
                "state": self._state,
                "mode": self._mode,
                **result,
            }

    def _build_status(self) -> dict[str, Any]:
        snapshot = self._service.snapshot_status()
        return {
            "state": self._state,
            "mode": self._mode,
            "total_count": snapshot["total_count"],
            "active_tracks": snapshot["active_tracks"],
            "fps": snapshot["fps"],
            "annotated_frame_b64": self._service.last_annotated_frame_b64,
            "events": snapshot["events"],
        }


def _decode_frame(frame_bytes: bytes) -> np.ndarray:
    buffer = np.frombuffer(frame_bytes, dtype=np.uint8)
    frame = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Frame invalido ou formato de imagem nao suportado.")
    return frame
