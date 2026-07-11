#!/usr/bin/env python3
"""
Egg Vision AI — Treinamento YOLOv8n
===================================
Script profissional para treinar o detector de ovos na esteira.

Dataset esperado (ou criado automaticamente):
    D:\\contador\\fotos\\
        images\\train\\
        images\\val\\
        labels\\train\\
        labels\\val\\
        dataset.yaml

Uso:
    python train.py
    python train.py --epochs 100 --batch 16 --imgsz 640
"""

from __future__ import annotations

import argparse
import logging
import random
import shutil
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Constantes do projeto
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DATASET_DIR = Path(r"D:\contador\fotos")
CLASS_NAME = "egg"
BASE_MODEL = "yolov8n.pt"
DEFAULT_EPOCHS = 100
DEFAULT_BATCH = 16
DEFAULT_IMGSZ = 640
VAL_RATIO = 0.20
SEED = 42

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("egg-vision-train")


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def resolve_device(preferred: str | None = None) -> str | int:
    """Retorna device CUDA (0) se disponivel; caso contrario 'cpu'."""
    if preferred is not None:
        return preferred if preferred == "cpu" else int(preferred)

    try:
        import torch

        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            logger.info("GPU CUDA detectada: %s (device=0)", name)
            return 0
        logger.warning("CUDA indisponivel. Treinamento seguira em CPU (mais lento).")
        return "cpu"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Falha ao inspecionar CUDA (%s). Usando CPU.", exc)
        return "cpu"


def list_images(directory: Path) -> list[Path]:
    return sorted(
        p
        for p in directory.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )


def has_yolo_structure(dataset_dir: Path) -> bool:
    required = [
        dataset_dir / "images" / "train",
        dataset_dir / "images" / "val",
        dataset_dir / "labels" / "train",
        dataset_dir / "labels" / "val",
    ]
    return all(path.is_dir() for path in required)


def ensure_yolo_dirs(dataset_dir: Path) -> None:
    for split in ("train", "val"):
        (dataset_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (dataset_dir / "labels" / split).mkdir(parents=True, exist_ok=True)


def sanitize_stem(path: Path) -> str:
    """Gera nome de arquivo estavel (sem espacos/caracteres problematicos)."""
    stem = path.stem
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in stem)
    cleaned = "_".join(part for part in cleaned.split("_") if part)
    return cleaned or "img"


def collect_loose_images(dataset_dir: Path) -> list[Path]:
    """Imagens soltas na raiz (ainda nao organizadas em images/train|val)."""
    loose: list[Path] = []
    for path in dataset_dir.iterdir():
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            loose.append(path)
    return sorted(loose)


def organize_dataset(dataset_dir: Path, val_ratio: float = VAL_RATIO, seed: int = SEED) -> dict[str, int]:
    """
    Cria a estrutura YOLO e distribui imagens soltas em train/val.
    Labels .txt com o mesmo stem sao movidos junto quando existirem.
    """
    ensure_yolo_dirs(dataset_dir)
    loose = collect_loose_images(dataset_dir)

    # Tambem considera imagens ja em subpastas fora do padrao YOLO
    nested = [
        p
        for p in list_images(dataset_dir)
        if "images\\train" not in str(p) and "images/train" not in str(p)
        and "images\\val" not in str(p) and "images/val" not in str(p)
        and p.parent == dataset_dir
    ]
    candidates = sorted({*loose, *nested}, key=lambda p: p.name.lower())

    if not candidates:
        train_imgs = list_images(dataset_dir / "images" / "train")
        val_imgs = list_images(dataset_dir / "images" / "val")
        if train_imgs or val_imgs:
            logger.info(
                "Estrutura YOLO ja populada: train=%s | val=%s",
                len(train_imgs),
                len(val_imgs),
            )
            return {"train": len(train_imgs), "val": len(val_imgs), "moved": 0}

        logger.error(
            "Nenhuma imagem encontrada em %s. Coloque fotos (.jpg/.jpeg/.png) nesta pasta.",
            dataset_dir,
        )
        raise FileNotFoundError(f"Sem imagens em {dataset_dir}")

    rng = random.Random(seed)
    rng.shuffle(candidates)
    val_count = max(1, int(round(len(candidates) * val_ratio))) if len(candidates) > 1 else 0
    val_set = set(candidates[:val_count])
    train_set = [p for p in candidates if p not in val_set]

    moved = 0
    for split, files in (("train", train_set), ("val", list(val_set))):
        for index, src in enumerate(files):
            stem = f"{sanitize_stem(src)}_{index:04d}"
            dest_img = dataset_dir / "images" / split / f"{stem}{src.suffix.lower()}"
            shutil.copy2(src, dest_img)

            # Label correspondente (mesmo nome, .txt) na raiz ou ao lado
            label_candidates = [
                src.with_suffix(".txt"),
                dataset_dir / "labels" / f"{src.stem}.txt",
                dataset_dir / f"{src.stem}.txt",
            ]
            label_src = next((p for p in label_candidates if p.is_file()), None)
            dest_lbl = dataset_dir / "labels" / split / f"{stem}.txt"
            if label_src is not None:
                shutil.copy2(label_src, dest_lbl)
            else:
                # Stub vazio: imagem de fundo (sem ovo) ou aguardando anotacao
                dest_lbl.write_text("", encoding="utf-8")
            moved += 1

    logger.info(
        "Dataset estruturado: %s imagens -> train=%s | val=%s",
        moved,
        len(train_set),
        len(val_set),
    )
    logger.info(
        "ORIENTACAO: cada imagem precisa de um .txt YOLO em labels/<split>/ "
        "com linhas no formato:  0  x_centro  y_centro  largura  altura  (valores 0-1)."
    )
    logger.info(
        "Ferramentas sugeridas para anotar: LabelImg, Roboflow, CVAT ou Ultralytics Annotator."
    )
    return {"train": len(train_set), "val": len(val_set), "moved": moved}


def count_labeled_boxes(labels_dir: Path) -> tuple[int, int]:
    """Retorna (arquivos_com_box, total_boxes)."""
    files_with = 0
    boxes = 0
    for path in labels_dir.glob("*.txt"):
        lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if lines:
            files_with += 1
            boxes += len(lines)
    return files_with, boxes


def _read_bgr(path: Path):
    import cv2
    import numpy as np

    data = np.fromfile(str(path), dtype=np.uint8)
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def _bbox_to_yolo(
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


def auto_label_dataset(dataset_dir: Path) -> dict[str, int]:
    """
    Gera labels YOLO (classe 0 = ovo) com o detector classico do Egg.
    Usado quando as fotos ainda nao tem anotacao manual.
    """
    egg_src = PROJECT_ROOT / "python" / "egg" / "src"
    if egg_src.exists() and str(egg_src) not in sys.path:
        sys.path.insert(0, str(egg_src))

    try:
        from egg_counter.config import RuntimeConfig
        from egg_counter.detection import ClassicBackend
    except ImportError as exc:
        raise RuntimeError(
            "Nao foi possivel importar egg_counter para auto-label. "
            "Rode: pip install -e python/egg"
        ) from exc

    detector = ClassicBackend(
        RuntimeConfig(backend="classic", normalize=False, reference_image=None)
    )

    stats = {"images": 0, "labeled": 0, "boxes": 0, "empty": 0}
    for split in ("train", "val"):
        images_dir = dataset_dir / "images" / split
        labels_dir = dataset_dir / "labels" / split
        labels_dir.mkdir(parents=True, exist_ok=True)
        for image_path in list_images(images_dir):
            stats["images"] += 1
            frame = _read_bgr(image_path)
            label_path = labels_dir / f"{image_path.stem}.txt"
            if frame is None:
                label_path.write_text("", encoding="utf-8")
                stats["empty"] += 1
                logger.warning("Imagem invalida (ignorada): %s", image_path.name)
                continue

            height, width = frame.shape[:2]
            detections = detector.detect(frame)
            lines: list[str] = []
            for det in detections:
                if det.label not in {"egg", "ovo"}:
                    continue
                xc, yc, bw, bh = _bbox_to_yolo(det.bbox, width, height)
                lines.append(f"0 {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")

            label_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
            if lines:
                stats["labeled"] += 1
                stats["boxes"] += len(lines)
            else:
                stats["empty"] += 1

    logger.info(
        "Auto-label concluido: %s imagens | %s com ovo | %s boxes | %s vazias",
        stats["images"],
        stats["labeled"],
        stats["boxes"],
        stats["empty"],
    )
    if stats["boxes"] == 0:
        raise RuntimeError(
            "Auto-label nao encontrou ovos nas fotos. "
            "Verifique as imagens ou anote manualmente."
        )
    return stats


def write_dataset_yaml(dataset_dir: Path) -> Path:
    """Gera dataset.yaml apontando para a pasta com classe 0: ovo."""
    yaml_path = dataset_dir / "dataset.yaml"
    content = (
        f"# Egg Vision AI — dataset YOLO\n"
        f"# Gerado automaticamente em {datetime.now():%Y-%m-%d %H:%M:%S}\n"
        f"path: {dataset_dir.as_posix()}\n"
        f"train: images/train\n"
        f"val: images/val\n"
        f"names:\n"
        f"  0: {CLASS_NAME}\n"
    )
    yaml_path.write_text(content, encoding="utf-8")
    logger.info("Arquivo dataset.yaml criado: %s", yaml_path)
    return yaml_path


def validate_dataset(dataset_dir: Path) -> None:
    train_imgs = list_images(dataset_dir / "images" / "train")
    val_imgs = list_images(dataset_dir / "images" / "val")
    if not train_imgs:
        raise RuntimeError("images/train esta vazio. Adicione imagens antes de treinar.")
    if not val_imgs:
        raise RuntimeError("images/val esta vazio. Precisa de ao menos 1 imagem de validacao.")

    train_labeled, train_boxes = count_labeled_boxes(dataset_dir / "labels" / "train")
    val_labeled, val_boxes = count_labeled_boxes(dataset_dir / "labels" / "val")

    logger.info("Imagens  | train=%s | val=%s", len(train_imgs), len(val_imgs))
    logger.info(
        "Labels   | train=%s arquivos com box (%s boxes) | val=%s arquivos com box (%s boxes)",
        train_labeled,
        train_boxes,
        val_labeled,
        val_boxes,
    )

    if train_boxes == 0:
        raise RuntimeError(
            "Nenhuma anotacao encontrada em labels/train.\n"
            "Anote os ovos no formato YOLO (classe 0 = ovo) antes de treinar.\n"
            "Exemplo de linha no .txt:  0 0.512 0.430 0.085 0.120"
        )


def export_best_weights(best_pt: Path, export_dir: Path) -> Path:
    export_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stamped = export_dir / f"egg_yolov8n_{stamp}.pt"
    latest = export_dir / "egg_yolov8n.pt"
    shutil.copy2(best_pt, stamped)
    shutil.copy2(best_pt, latest)

    # Copia tambem para o processador do Egg, se existir
    processador_models = PROJECT_ROOT / "python" / "egg" / "models"
    if processador_models.parent.exists():
        processador_models.mkdir(parents=True, exist_ok=True)
        shutil.copy2(best_pt, processador_models / "egg_yolov8n.pt")
        logger.info("Pesos copiados para o processador: %s", processador_models / "egg_yolov8n.pt")

    logger.info("Pesos salvos: %s", latest)
    logger.info("Copia versionada: %s", stamped)
    return latest


def train(
    dataset_dir: Path,
    *,
    epochs: int,
    batch: int,
    imgsz: int,
    model_name: str,
    device: str | int,
    project: Path,
    run_name: str,
    workers: int,
) -> Path:
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError(
            "Pacote ultralytics nao encontrado. Instale com:\n"
            "  pip install ultralytics opencv-python pyyaml torch"
        ) from exc

    yaml_path = dataset_dir / "dataset.yaml"
    if not yaml_path.exists():
        yaml_path = write_dataset_yaml(dataset_dir)

    logger.info("=" * 72)
    logger.info("Egg Vision AI | Treinamento YOLOv8n")
    logger.info("=" * 72)
    logger.info("Dataset : %s", dataset_dir)
    logger.info("Modelo  : %s", model_name)
    logger.info("Epochs  : %s | batch=%s | imgsz=%s | device=%s", epochs, batch, imgsz, device)
    logger.info("Saida   : %s/%s", project, run_name)
    logger.info("=" * 72)

    model = YOLO(model_name)
    results = model.train(
        data=str(yaml_path),
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        device=device,
        project=str(project),
        name=run_name,
        exist_ok=True,
        workers=workers,
        patience=25,
        save=True,
        plots=False,  # evita crash nativo ocasional no Windows
        verbose=True,
        pretrained=True,
        optimizer="auto",
        cos_lr=True,
        close_mosaic=10,
        amp=False if device == "cpu" else True,
        cache=False,
        seed=SEED,
    )

    best = Path(results.save_dir) / "weights" / "best.pt"
    last = Path(results.save_dir) / "weights" / "last.pt"
    if not best.exists():
        if last.exists():
            logger.warning("best.pt ausente; usando last.pt")
            best = last
        else:
            raise RuntimeError(f"Treino finalizou sem pesos em {results.save_dir / 'weights'}")

    return best


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Egg Vision AI — treina YOLOv8n para detectar ovos na esteira.",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_DIR,
        help=rf"Pasta do dataset (padrao: {DEFAULT_DATASET_DIR})",
    )
    parser.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS)
    parser.add_argument("--batch", type=int, default=DEFAULT_BATCH)
    parser.add_argument("--imgsz", type=int, default=DEFAULT_IMGSZ)
    parser.add_argument("--model", default=BASE_MODEL, help="Peso base Ultralytics")
    parser.add_argument(
        "--device",
        default=None,
        help="Forca device (0, 0,1, cpu). Padrao: auto-detecta CUDA.",
    )
    parser.add_argument(
        "--project",
        type=Path,
        default=PROJECT_ROOT / "runs" / "egg-vision",
        help="Pasta de runs do Ultralytics",
    )
    parser.add_argument("--name", default="yolov8n-ovo", help="Nome do experimento")
    parser.add_argument(
        "--export-dir",
        type=Path,
        default=PROJECT_ROOT / "models",
        help="Onde salvar egg_yolov8n.pt final",
    )
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument(
        "--skip-organize",
        action="store_true",
        help="Nao reorganiza imagens soltas; exige estrutura YOLO ja pronta.",
    )
    parser.add_argument(
        "--auto-label",
        action="store_true",
        help="Gera labels YOLO automaticamente com o detector classico do Egg.",
    )
    parser.add_argument(
        "--allow-empty-labels",
        action="store_true",
        help="Permite treinar mesmo sem boxes (nao recomendado).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset_dir = args.dataset.resolve()

    try:
        if not dataset_dir.exists():
            dataset_dir.mkdir(parents=True, exist_ok=True)
            logger.warning("Pasta criada: %s", dataset_dir)
            logger.error(
                "Coloque as fotos em %s e execute novamente. "
                "Depois anote os ovos (labels YOLO).",
                dataset_dir,
            )
            return 2

        if has_yolo_structure(dataset_dir):
            logger.info("Estrutura YOLO encontrada em %s", dataset_dir)
            if not args.skip_organize and collect_loose_images(dataset_dir):
                logger.info("Imagens soltas detectadas na raiz — organizando em train/val...")
                organize_dataset(dataset_dir)
        else:
            logger.warning(
                "Estrutura YOLO ausente. Criando images/train|val e labels/train|val..."
            )
            organize_dataset(dataset_dir)

        write_dataset_yaml(dataset_dir)

        train_boxes = count_labeled_boxes(dataset_dir / "labels" / "train")[1]
        if args.auto_label or train_boxes == 0:
            logger.info("Iniciando auto-label (classe 0 = ovo)...")
            auto_label_dataset(dataset_dir)

        try:
            validate_dataset(dataset_dir)
        except RuntimeError as exc:
            if args.allow_empty_labels and "Nenhuma anotacao" in str(exc):
                logger.warning("Prosseguindo sem labels (--allow-empty-labels). Resultado sera ruim.")
            else:
                logger.error("%s", exc)
                logger.error(
                    "Proximos passos:\n"
                    "  1) Anote as imagens em D:\\contador\\fotos\\images\\train e val\n"
                    "  2) Salve labels espelhados em labels\\train e labels\\val\n"
                    "  3) Classe unica: 0 = ovo\n"
                    "  4) Rode novamente: python train.py --auto-label"
                )
                return 3

        device = resolve_device(args.device)
        # Em CPU, batch 16 pode estourar memoria; reduz automaticamente
        batch = args.batch
        if device == "cpu" and batch > 8:
            logger.warning("CPU detectada: reduzindo batch de %s para 8.", batch)
            batch = 8

        best = train(
            dataset_dir,
            epochs=args.epochs,
            batch=batch,
            imgsz=args.imgsz,
            model_name=args.model,
            device=device,
            project=args.project,
            run_name=args.name,
            workers=0 if device == "cpu" else args.workers,
        )
        export_best_weights(best, args.export_dir.resolve())
        update_processador_runtime(CLASS_NAME)

        logger.info("=" * 72)
        logger.info("TREINO CONCLUIDO COM SUCESSO")
        logger.info("Para usar no processador Egg:")
        logger.info("  backend: ultralytics")
        logger.info("  model_path: models/egg_yolov8n.pt")
        logger.info("  target_label: %s", CLASS_NAME)
        logger.info("=" * 72)
        return 0

    except KeyboardInterrupt:
        logger.warning("Treino interrompido pelo usuario.")
        return 130
    except Exception as exc:  # noqa: BLE001
        logger.exception("Falha no treinamento: %s", exc)
        return 1


def update_processador_runtime(target_label: str) -> None:
    """Aponta os YAMLs do processador para o YOLO treinado (nao sobrescreve ensemble)."""
    config_dir = PROJECT_ROOT / "python" / "egg" / "config"
    if not config_dir.is_dir():
        return

    files = [
        config_dir / "runtime.yaml",
        config_dir / "runtime.video-testes.yaml",
        config_dir / "runtime.video-padrao.yaml",
        config_dir / "runtime.video-ovos3.yaml",
    ]
    for path in files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if "backend: ensemble" in text or "model_paths:" in text:
            logger.info("Runtime ensemble preservado (nao sobrescrito): %s", path.name)
            continue
        lines = []
        for line in text.splitlines():
            if line.startswith("backend:"):
                lines.append("backend: ultralytics")
            elif line.startswith("model_path:"):
                lines.append("model_path: models/egg_yolov8n.pt")
            elif line.startswith("target_label:"):
                lines.append(f"target_label: {target_label}")
            elif line.startswith("confidence:"):
                lines.append("confidence: 0.25")
            else:
                lines.append(line)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        logger.info("Runtime atualizado: %s", path.name)


if __name__ == "__main__":
    sys.exit(main())
