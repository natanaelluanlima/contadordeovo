from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path

import cv2

logger = logging.getLogger(__name__)

_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".m4v"}


@dataclass(slots=True)
class ExtractionResult:
    video_path: Path
    frames_saved: int
    fps: float
    duration_seconds: float
    output_dir: Path


def extract_frames_from_video(
    video_path: Path | str,
    output_dir: Path | str,
    *,
    interval_seconds: float = 1.0,
    image_format: str = "jpg",
    jpeg_quality: int = 95,
    prefix: str | None = None,
) -> ExtractionResult:
    """Extrai frames de um video em intervalos regulares (padrao: 1 fps amostral).

    Usa o FPS do video para calcular o passo entre frames, evitando salvar
    frames consecutivos quase identicos e melhorando a diversidade do dataset.
    """
    if interval_seconds <= 0:
        raise ValueError("interval_seconds deve ser maior que zero.")

    video_path = Path(video_path)
    output_dir = Path(output_dir)
    if not video_path.is_file():
        raise FileNotFoundError(f"Video nao encontrado: {video_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    stem = prefix or video_path.stem
    extension = image_format.lstrip(".").lower()

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Nao foi possivel abrir o video: {video_path}")

    try:
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
        if fps <= 0:
            fps = 30.0
            logger.warning(
                "FPS invalido em %s; usando fallback %.1f",
                video_path.name,
                fps,
            )

        frame_step = max(1, int(round(fps * interval_seconds)))
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration_seconds = total_frames / fps if total_frames > 0 else 0.0

        encode_params: list[int] = []
        if extension in {"jpg", "jpeg"}:
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]

        saved = 0
        frame_index = 0
        while True:
            ok, frame = capture.read()
            if not ok:
                break

            if frame_index % frame_step == 0:
                second_mark = int(round(frame_index / fps))
                filename = f"{stem}_{second_mark:06d}.{extension}"
                destination = output_dir / filename
                if not cv2.imwrite(str(destination), frame, encode_params):
                    raise RuntimeError(f"Falha ao salvar frame: {destination}")
                saved += 1

            frame_index += 1
    finally:
        capture.release()

    logger.info(
        "Extraidos %s frames de %s (fps=%.2f, intervalo=%.2fs) -> %s",
        saved,
        video_path.name,
        fps,
        interval_seconds,
        output_dir,
    )
    return ExtractionResult(
        video_path=video_path,
        frames_saved=saved,
        fps=fps,
        duration_seconds=duration_seconds,
        output_dir=output_dir,
    )


def extract_frames_from_videos(
    videos_dir: Path | str,
    output_dir: Path | str,
    *,
    interval_seconds: float = 1.0,
    image_format: str = "jpg",
    jpeg_quality: int = 95,
    recursive: bool = False,
) -> list[ExtractionResult]:
    """Processa todos os videos de uma pasta e salva frames no dataset."""
    videos_dir = Path(videos_dir)
    output_dir = Path(output_dir)
    if not videos_dir.is_dir():
        raise NotADirectoryError(f"Pasta de videos nao encontrada: {videos_dir}")

    pattern = "**/*" if recursive else "*"
    videos = sorted(
        path
        for path in videos_dir.glob(pattern)
        if path.is_file() and path.suffix.lower() in _VIDEO_EXTENSIONS
    )
    if not videos:
        raise FileNotFoundError(f"Nenhum video encontrado em: {videos_dir}")

    images_dir = output_dir / "images"
    results: list[ExtractionResult] = []
    for video_path in videos:
        video_output = images_dir / video_path.stem
        results.append(
            extract_frames_from_video(
                video_path,
                video_output,
                interval_seconds=interval_seconds,
                image_format=image_format,
                jpeg_quality=jpeg_quality,
            )
        )

    labels_dir = output_dir / "labels"
    labels_dir.mkdir(parents=True, exist_ok=True)
    return results


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    if args.video:
        result = extract_frames_from_video(
            args.video,
            Path(args.output) / "images" / Path(args.video).stem,
            interval_seconds=args.interval,
            image_format=args.format,
            jpeg_quality=args.quality,
        )
        Path(args.output, "labels").mkdir(parents=True, exist_ok=True)
        print(
            f"OK: {result.frames_saved} frames de {result.video_path.name} "
            f"em {result.output_dir}"
        )
        return

    results = extract_frames_from_videos(
        args.videos_dir,
        args.output,
        interval_seconds=args.interval,
        image_format=args.format,
        jpeg_quality=args.quality,
        recursive=args.recursive,
    )
    total = sum(item.frames_saved for item in results)
    print(f"OK: {total} frames de {len(results)} video(s) em {args.output}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extrai frames de videos em intervalo regular (padrao 1s) "
            "para montar dataset de treinamento YOLO."
        )
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--video",
        type=Path,
        help="Caminho de um unico video de entrada.",
    )
    source.add_argument(
        "--videos-dir",
        type=Path,
        help="Pasta com videos de entrada.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dataset"),
        help="Pasta de saida do dataset (cria images/ e labels/). Padrao: dataset/",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Intervalo em segundos entre frames extraidos. Padrao: 1.0",
    )
    parser.add_argument(
        "--format",
        choices=("jpg", "jpeg", "png"),
        default="jpg",
        help="Formato das imagens salvas. Padrao: jpg",
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=95,
        help="Qualidade JPEG (1-100). Padrao: 95",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Busca videos recursivamente em --videos-dir.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
