from __future__ import annotations

import argparse
import logging
import random
import shutil
from pathlib import Path

import cv2
import numpy as np
import yaml

from egg_counter.config import RuntimeConfig
from egg_counter.dataset import extract_frames_from_video
from egg_counter.detection import ClassicBackend

logger = logging.getLogger(__name__)

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
_SKIP_NAME_PARTS = (
    "mask",
    "hsv",
    "sat",
    "ell",
    "overlay",
    "brown_mask",
    "reference-empty",
)


def _read_image(path: Path) -> np.ndarray | None:
    """Le imagem com suporte a caminhos Unicode no Windows."""
    try:
        data = np.fromfile(str(path), dtype=np.uint8)
    except OSError:
        return None
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def _write_image(path: Path, frame: np.ndarray, jpeg_quality: int = 95) -> bool:
    ok, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
    if not ok:
        return False
    buffer.tofile(str(path))
    return True


def _is_training_image(path: Path) -> bool:
    name = path.name.lower()
    if path.suffix.lower() not in _IMAGE_EXTENSIONS:
        return False
    return not any(part in name for part in _SKIP_NAME_PARTS)


def collect_source_images(roots: list[Path]) -> list[Path]:
    images: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        if root.is_file() and _is_training_image(root):
            key = str(root.resolve())
            if key not in seen:
                seen.add(key)
                images.append(root)
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or not _is_training_image(path):
                continue
            key = str(path.resolve())
            if key in seen:
                continue
            seen.add(key)
            images.append(path)
    return images


def bbox_to_yolo(
    bbox: tuple[int, int, int, int],
    width: int,
    height: int,
) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = bbox
    x1 = max(0, min(width - 1, x1))
    x2 = max(0, min(width, x2))
    y1 = max(0, min(height - 1, y1))
    y2 = max(0, min(height, y2))
    bw = max(1, x2 - x1)
    bh = max(1, y2 - y1)
    xc = (x1 + x2) / 2.0 / width
    yc = (y1 + y2) / 2.0 / height
    return xc, yc, bw / width, bh / height


def auto_label_image(
    image_path: Path,
    detector: ClassicBackend,
    images_out: Path,
    labels_out: Path,
    stem: str,
) -> int | None:
    frame = _read_image(image_path)
    if frame is None:
        logger.warning("Ignorando imagem invalida: %s", image_path)
        return None

    height, width = frame.shape[:2]
    detections = detector.detect(frame)
    destination = images_out / f"{stem}.jpg"
    if not _write_image(destination, frame):
        raise RuntimeError(f"Falha ao salvar imagem: {destination}")

    label_path = labels_out / f"{stem}.txt"
    lines: list[str] = []
    for detection in detections:
        if detection.label != "egg":
            continue
        xc, yc, bw, bh = bbox_to_yolo(detection.bbox, width, height)
        lines.append(f"0 {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")
    label_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return len(lines)


def build_dataset(
    source_images: list[Path],
    dataset_dir: Path,
    *,
    val_ratio: float = 0.2,
    seed: int = 42,
    keep_empty: bool = True,
    max_empty: int = 20,
) -> dict[str, int]:
    detector = ClassicBackend(
        RuntimeConfig(backend="classic", normalize=False, reference_image=None)
    )

    staging_images = dataset_dir / "_staging" / "images"
    staging_labels = dataset_dir / "_staging" / "labels"
    if staging_images.exists():
        shutil.rmtree(staging_images.parent)
    staging_images.mkdir(parents=True)
    staging_labels.mkdir(parents=True)

    labeled: list[tuple[str, int]] = []
    empty: list[str] = []
    for index, image_path in enumerate(source_images):
        stem = f"{image_path.stem}_{index:04d}"
        count = auto_label_image(
            image_path,
            detector,
            staging_images,
            staging_labels,
            stem,
        )
        if count is None:
            continue
        if count > 0:
            labeled.append((stem, count))
        else:
            empty.append(stem)

    if keep_empty and empty:
        random.Random(seed).shuffle(empty)
        empty = empty[:max_empty]
    else:
        empty = []

    selected = [stem for stem, _ in labeled] + empty
    if not selected:
        raise RuntimeError(
            "Nenhuma imagem util para treino. Verifique as fotos de entrada."
        )

    random.Random(seed).shuffle(selected)
    val_count = max(1, int(round(len(selected) * val_ratio))) if len(selected) > 1 else 0
    val_stems = set(selected[:val_count])
    train_stems = [stem for stem in selected if stem not in val_stems]

    for split, stems in (("train", train_stems), ("val", list(val_stems))):
        images_dir = dataset_dir / "images" / split
        labels_dir = dataset_dir / "labels" / split
        if images_dir.exists():
            shutil.rmtree(images_dir)
        if labels_dir.exists():
            shutil.rmtree(labels_dir)
        images_dir.mkdir(parents=True)
        labels_dir.mkdir(parents=True)
        for stem in stems:
            shutil.copy2(staging_images / f"{stem}.jpg", images_dir / f"{stem}.jpg")
            shutil.copy2(staging_labels / f"{stem}.txt", labels_dir / f"{stem}.txt")

    shutil.rmtree(staging_images.parent)

    data_yaml = {
        "path": str(dataset_dir.resolve()),
        "train": "images/train",
        "val": "images/val",
        "names": {0: "egg"},
    }
    yaml_path = dataset_dir / "data.yaml"
    yaml_path.write_text(
        yaml.safe_dump(data_yaml, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    egg_boxes = sum(count for _, count in labeled)
    stats = {
        "sources": len(source_images),
        "train": len(train_stems),
        "val": len(val_stems),
        "with_eggs": len(labeled),
        "empty": len(empty),
        "egg_boxes": egg_boxes,
    }
    logger.info("Dataset pronto: %s", stats)
    return stats


def train_yolo(
    data_yaml: Path,
    *,
    model_name: str = "yolov8n.pt",
    epochs: int = 50,
    imgsz: int = 640,
    batch: int = 8,
    project: Path = Path("runs"),
    name: str = "egg_yolov8n",
    device: str = "cpu",
) -> Path:
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError(
            "Ultralytics nao esta instalado. Rode `pip install -e .` no projeto."
        ) from exc

    model = YOLO(model_name)
    results = model.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        project=str(project),
        name=name,
        exist_ok=True,
        device=device,
        workers=0,
        patience=15,
        verbose=True,
    )
    best = Path(results.save_dir) / "weights" / "best.pt"
    if not best.exists():
        raise RuntimeError(f"Treino finalizou sem weights/best.pt em {results.save_dir}")
    return best


def export_model(best_weights: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best_weights, destination)
    logger.info("Modelo exportado para %s", destination)
    return destination


def default_source_roots(project_root: Path) -> list[Path]:
    return [
        project_root / "videos",
        project_root / "config" / "debug-erro",
        project_root / "config" / "debug-erro1",
        project_root / "config" / "debug-erro2",
        project_root / "dataset" / "images",
    ]


def prepare_frames_from_videos(project_root: Path, interval_seconds: float = 1.0) -> list[Path]:
    videos_dir = project_root / "videos"
    extracted_root = project_root / "dataset" / "images" / "_extracted"
    extracted: list[Path] = []
    if not videos_dir.exists():
        return extracted

    for video in sorted(videos_dir.glob("*")):
        if video.suffix.lower() not in {".mp4", ".avi", ".mov", ".mkv", ".webm"}:
            continue
        out_dir = extracted_root / video.stem
        result = extract_frames_from_video(
            video,
            out_dir,
            interval_seconds=interval_seconds,
        )
        extracted.extend(sorted(out_dir.glob("*.jpg")))
        logger.info("Video %s -> %s frames", video.name, result.frames_saved)
    return extracted


def run_pipeline(args: argparse.Namespace) -> Path:
    project_root = Path(args.project_root).resolve()
    dataset_dir = Path(args.dataset).resolve()
    models_dir = Path(args.models_dir).resolve()

    if args.extract_videos:
        prepare_frames_from_videos(project_root, interval_seconds=args.interval)

    roots = [Path(item) for item in args.sources] if args.sources else default_source_roots(project_root)
    # Inclui analysis frames do config (sem masks)
    analysis_images = [
        path
        for path in (project_root / "config").glob("analysis-*.jpg")
        if _is_training_image(path)
    ]
    source_images = collect_source_images(roots) + analysis_images
    # Dedup por resolve
    unique: dict[str, Path] = {str(path.resolve()): path for path in source_images}
    source_images = list(unique.values())
    logger.info("Imagens candidatas: %s", len(source_images))

    stats = build_dataset(
        source_images,
        dataset_dir,
        val_ratio=args.val_ratio,
        seed=args.seed,
        keep_empty=not args.no_empty,
        max_empty=args.max_empty,
    )
    if stats["with_eggs"] == 0:
        raise RuntimeError(
            "O detector classico nao encontrou ovos nas fotos. "
            "Revise as imagens de entrada antes de treinar."
        )

    best = train_yolo(
        dataset_dir / "data.yaml",
        model_name=args.base_model,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project=Path(args.runs_dir),
        name=args.run_name,
        device=args.device,
    )
    return export_model(best, models_dir / "egg_yolov8n.pt")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Monta dataset YOLO a partir das fotos (auto-label com detector classico) "
            "e treina YOLOv8 para detectar ovos."
        )
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="Raiz do projeto python/egg. Padrao: .",
    )
    parser.add_argument(
        "--sources",
        nargs="*",
        default=None,
        help="Pastas/arquivos de imagens. Padrao: videos/, config/debug-erro*, dataset/images/",
    )
    parser.add_argument(
        "--dataset",
        default="dataset/yolo-eggs",
        help="Pasta do dataset YOLO gerado.",
    )
    parser.add_argument(
        "--models-dir",
        default="models",
        help="Pasta onde salvar egg_yolov8n.pt",
    )
    parser.add_argument(
        "--runs-dir",
        default="runs",
        help="Pasta de saida do Ultralytics.",
    )
    parser.add_argument("--run-name", default="egg_yolov8n")
    parser.add_argument("--base-model", default="yolov8n.pt")
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-empty", type=int, default=20)
    parser.add_argument("--no-empty", action="store_true")
    parser.add_argument(
        "--extract-videos",
        action="store_true",
        help="Extrai 1 frame/s dos videos em videos/ antes do treino.",
    )
    parser.add_argument("--interval", type=float, default=1.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    model_path = run_pipeline(args)
    print(f"Modelo treinado: {model_path}")


if __name__ == "__main__":
    main()
