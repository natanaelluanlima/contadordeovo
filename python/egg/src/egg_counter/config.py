from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


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
    data = _load_yaml(config_path)
    reference_image = data.get("reference_image")
    if isinstance(reference_image, str):
        reference_image = _resolve_relative_path(reference_image, config_path)

    model_path = str(data.get("model_path", "yolov8n.pt"))
    if not Path(model_path).is_absolute() and "/" in model_path.replace("\\", "/"):
        model_path = _resolve_relative_path(model_path, config_path)

    return RuntimeConfig(
        backend=str(data.get("backend", "ultralytics")),
        model_path=model_path,
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
