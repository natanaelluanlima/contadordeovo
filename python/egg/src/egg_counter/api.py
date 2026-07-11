from __future__ import annotations

from typing import Any

from fastapi import APIRouter, FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from egg_counter.session import ProcessadorSession

ROOT_PREFIX = "/gruponeural/egg/processador"


class FrameB64Request(BaseModel):
    image_b64: str


def create_app(session: ProcessadorSession) -> FastAPI:
    app = FastAPI(title="Egg Processador", version="0.1.0")
    router = APIRouter(prefix=ROOT_PREFIX)

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/v1/session/status")
    def session_status() -> dict[str, Any]:
        return session.status()

    @router.post("/v1/session/start")
    def session_start(body: dict[str, Any] | None = None) -> dict[str, Any]:
        return session.start(body)

    @router.post("/v1/session/stop")
    def session_stop() -> dict[str, Any]:
        return session.stop()

    @router.post("/v1/session/frame")
    async def session_frame(file: UploadFile = File(...)) -> dict[str, Any]:
        try:
            frame_bytes = await file.read()
            return session.process_frame_bytes(frame_bytes)
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/v1/session/frame-b64")
    def session_frame_b64(body: FrameB64Request) -> dict[str, Any]:
        try:
            if not body.image_b64 or not str(body.image_b64).strip():
                raise ValueError("image_b64 vazio.")
            return session.process_frame_b64(body.image_b64)
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=f"Falha ao processar frame: {exc}") from exc

    app.include_router(router)
    return app
