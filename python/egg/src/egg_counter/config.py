from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


def _load_dotenv(path: Path) -> None:
    """Carrega KEY=VALUE de um .env sem sobrescrever variaveis ja definidas."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass(slots=True)
class RoiConfig:
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0


ExcludeZoneConfig = RoiConfig


@dataclass(slots=True)
class LineConfig:
    x1: int = 0
    y1: int = 0
    x2: int = 0
    y2: int = 0
    direction: str = "top_to_bottom"


@dataclass(slots=True)
class CameraConfig:
    source: int | str = 0
    width: int = 1280
    height: int = 720
    fps: int = 30
    show_window: bool = True
    crop_roi: bool = True
    roi: RoiConfig = field(default_factory=RoiConfig)
    line: LineConfig = field(default_factory=LineConfig)
    exclude_zones: list[RoiConfig] = field(default_factory=list)


@dataclass(slots=True)
class RuntimeConfig:
    backend: str = "ultralytics"
    model_path: str = "yolov8n.pt"
    model_paths: list[str] = field(default_factory=list)
    confidence: float = 0.35
    iou: float = 0.45
    target_label: str | None = None
    match_distance: float = 90.0
    max_missing: int = 12
    normalize: bool = True
    reference_image: str | None = None
    diff_threshold: float = 55.0
    api_host: str = "0.0.0.0"
    api_port: int = 9002
    roboflow_api_url: str = "https://detect.roboflow.com"
    roboflow_api_key: str | None = None
    roboflow_workspace: str | None = None
    roboflow_workflow_id: str | None = None
    ensemble_iou: float = 0.45
    ensemble_solo_confidence: float = 0.55


def load_named_video_profile(name: str, config_dir: str | Path = "config") -> tuple[CameraConfig, RuntimeConfig]:
    base = Path(config_dir)
    return (
        load_camera_config(base / f"camera.video-{name}.yaml"),
        load_runtime_config(base / f"runtime.video-{name}.yaml"),
    )


def detect_video_profile(width: int, height: int) -> str | None:
    if abs(width - 960) <= 48 and abs(height - 540) <= 48:
        return "padrao"
    if abs(width - 848) <= 48 and abs(height - 478) <= 48:
        return "testes"
    # TESTE 5.mp4 e similares (640x474 / 640x480)
    if abs(width - 640) <= 32 and abs(height - 480) <= 32:
        return "testes"
    return None


def load_camera_config(path: str | Path) -> CameraConfig:
    config_path = Path(path).resolve()
    data = _load_yaml(config_path)
    source = _parse_source(data.get("source", 0))
    if isinstance(source, str) and not source.isdigit() and not source.startswith(("rtsp://", "http://", "https://")):
        source = _resolve_relative_path(source, config_path)

    return CameraConfig(
        source=source,
        width=int(data.get("width", 1280)),
        height=int(data.get("height", 720)),
        fps=int(data.get("fps", 30)),
        show_window=bool(data.get("show_window", True)),
        crop_roi=bool(data.get("crop_roi", True)),
        roi=RoiConfig(**data.get("roi", {})),
        line=LineConfig(**data.get("line", {})),
        exclude_zones=[RoiConfig(**zone) for zone in data.get("exclude_zones", [])],
    )


def load_runtime_config(path: str | Path) -> RuntimeConfig:
    config_path = Path(path).resolve()
    project_root = _find_project_root(config_path)
    _load_dotenv(project_root / ".env")
    _load_dotenv(project_root.parent.parent / ".env")

    data = _load_yaml(config_path)
    reference_image = data.get("reference_image")
    if isinstance(reference_image, str):
        reference_image = _resolve_relative_path(reference_image, config_path)

    model_path = str(data.get("model_path", "yolov8n.pt"))
    if not Path(model_path).is_absolute() and "/" in model_path.replace("\\", "/"):
        model_path = _resolve_relative_path(model_path, config_path)

    raw_paths = data.get("model_paths") or []
    model_paths: list[str] = []
    if isinstance(raw_paths, list):
        for item in raw_paths:
            path_value = str(item)
            if not Path(path_value).is_absolute() and "/" in path_value.replace("\\", "/"):
                path_value = _resolve_relative_path(path_value, config_path)
            model_paths.append(path_value)

    api_key = data.get("roboflow_api_key") or os.environ.get("ROBOFLOW_API_KEY")
    workspace = data.get("roboflow_workspace") or os.environ.get("ROBOFLOW_WORKSPACE")
    workflow_id = data.get("roboflow_workflow_id") or os.environ.get("ROBOFLOW_WORKFLOW_ID")

    return RuntimeConfig(
        backend=str(data.get("backend", "ultralytics")),
        model_path=model_path,
        model_paths=model_paths,
        confidence=float(data.get("confidence", 0.35)),
        iou=float(data.get("iou", 0.45)),
        target_label=data.get("target_label"),
        match_distance=float(data.get("match_distance", 90.0)),
        max_missing=int(data.get("max_missing", 12)),
        normalize=bool(data.get("normalize", True)),
        reference_image=reference_image,
        diff_threshold=float(data.get("diff_threshold", 55.0)),
        api_host=str(data.get("api_host", "0.0.0.0")),
        api_port=int(data.get("api_port", 9002)),
        roboflow_api_url=str(
            data.get("roboflow_api_url")
            or os.environ.get("ROBOFLOW_API_URL")
            or "https://detect.roboflow.com"
        ),
        roboflow_api_key=str(api_key) if api_key else None,
        roboflow_workspace=str(workspace) if workspace else None,
        roboflow_workflow_id=str(workflow_id) if workflow_id else None,
        ensemble_iou=float(data.get("ensemble_iou", 0.45)),
        ensemble_solo_confidence=float(data.get("ensemble_solo_confidence", 0.55)),
    )


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Arquivo de configuracao invalido: {path}")
    return payload


def _find_project_root(config_path: Path) -> Path:
    for parent in (config_path.parent, *config_path.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    return config_path.parent


def _resolve_relative_path(value: str, config_path: Path) -> str:
    candidate = Path(value)
    if candidate.is_absolute():
        return str(candidate)
    base = _find_project_root(config_path)
    return str((base / candidate).resolve())


def _parse_source(value: Any) -> int | str:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return str(value)
