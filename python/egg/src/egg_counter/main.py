from __future__ import annotations

import argparse
import logging
from dataclasses import replace
from threading import Thread

from egg_counter.config import load_camera_config, load_runtime_config
from egg_counter.service import EggCounterService

logger = logging.getLogger(__name__)


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    camera = load_camera_config(args.camera_config)
    runtime = load_runtime_config(args.runtime_config)

    if args.source is not None:
        camera = replace(camera, source=_parse_source_override(args.source))
    if args.no_display:
        camera = replace(camera, show_window=False)

    service = EggCounterService(camera=camera, runtime=runtime)

    if args.serve_api:
        start_api_thread(service, runtime.api_host, runtime.api_port)

    logger.info("Iniciando pipeline de contagem com modelo %s", runtime.model_path)
    service.process_stream(max_frames=args.max_frames, display=not args.no_display)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MVP de contagem de ovos em esteira.")
    parser.add_argument(
        "--camera-config",
        default="config/camera.yaml",
        help="Caminho do arquivo YAML com configuracao da camera.",
    )
    parser.add_argument(
        "--runtime-config",
        default="config/runtime.yaml",
        help="Caminho do arquivo YAML com configuracao de runtime.",
    )
    parser.add_argument(
        "--source",
        default=None,
        help="Override para camera/video. Ex.: 0, rtsp://..., /path/video.mp4",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Limita a quantidade de frames processados, util para smoke tests.",
    )
    parser.add_argument(
        "--serve-api",
        action="store_true",
        help="Sobe uma API local com endpoints /health e /status.",
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Executa sem abrir a janela de debug.",
    )
    return parser.parse_args()


def start_api_thread(service: EggCounterService, host: str, port: int) -> None:
    def runner() -> None:
        try:
            import uvicorn
            from fastapi import FastAPI
        except ImportError as exc:
            raise RuntimeError(
                "Uvicorn nao esta instalado. Rode `pip install -e .` no projeto."
            ) from exc

        app = FastAPI(title="Egg Counter API", version="0.1.0")

        @app.get("/health")
        def health() -> dict[str, str]:
            return {"status": "ok"}

        @app.get("/status")
        def status() -> dict[str, object]:
            return service.snapshot_status()

        uvicorn.run(app, host=host, port=port, log_level="info")

    thread = Thread(target=runner, daemon=True)
    thread.start()
    logger.info("API local iniciada em http://%s:%s", host, port)


def _parse_source_override(value: str) -> int | str:
    return int(value) if value.isdigit() else value


if __name__ == "__main__":
    main()
