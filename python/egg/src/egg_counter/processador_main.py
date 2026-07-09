from __future__ import annotations

import argparse
import logging

import uvicorn

from egg_counter.api import create_app
from egg_counter.config import load_camera_config, load_runtime_config
from egg_counter.session import ProcessadorSession

logger = logging.getLogger(__name__)


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    camera = load_camera_config(args.camera_config)
    runtime = load_runtime_config(args.runtime_config)
    session = ProcessadorSession(camera=camera, runtime=runtime)
    app = create_app(session)

    logger.info(
        "Processador iniciado em http://%s:%s/gruponeural/egg/processador",
        runtime.api_host,
        runtime.api_port,
    )
    uvicorn.run(app, host=runtime.api_host, port=runtime.api_port, log_level="info")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="API do processador de contagem de ovos consumida pelo BFF."
    )
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
    return parser.parse_args()


if __name__ == "__main__":
    main()
