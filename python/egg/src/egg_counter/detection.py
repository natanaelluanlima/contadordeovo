from __future__ import annotations

import logging
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from egg_counter.config import RuntimeConfig
from egg_counter.models import Detection

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class _FrameCache:
    gray: np.ndarray
    hsv: np.ndarray
    hole_radius: float
    frame_hole_score: float
    reference: np.ndarray | None
    reference_aligned: bool


def _bbox_overlap_ratio(
    box_a: tuple[int, int, int, int],
    box_b: tuple[int, int, int, int],
) -> float:
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
    if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
        return 0.0

    intersection = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    smaller_area = min(area_a, area_b)
    if smaller_area <= 0:
        return 0.0
    return intersection / smaller_area


class InferenceBackend(ABC):
    @abstractmethod
    def detect(self, frame: np.ndarray) -> list[Detection]:
        """Executa a inferencia no frame."""


class UltralyticsBackend(InferenceBackend):
    def __init__(self, runtime: RuntimeConfig) -> None:
        self.runtime = runtime
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                "Ultralytics nao esta instalado. Rode `pip install -e .` no projeto."
            ) from exc

        self.model = YOLO(runtime.model_path)
        self._model_names = self.model.names

    def detect(self, frame: np.ndarray) -> list[Detection]:
        results = self.model.predict(
            source=frame,
            conf=self.runtime.confidence,
            iou=self.runtime.iou,
            verbose=False,
        )

        detections: list[Detection] = []
        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue

            for box in boxes:
                class_id = int(box.cls[0].item())
                label = self._resolve_label(class_id)
                if self.runtime.target_label and not _labels_match(label, self.runtime.target_label):
                    continue

                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append(
                    Detection(
                        bbox=(int(x1), int(y1), int(x2), int(y2)),
                        confidence=float(box.conf[0].item()),
                        label=label,
                    )
                )
        return detections

    def _resolve_label(self, class_id: int) -> str:
        if isinstance(self._model_names, dict):
            return str(self._model_names.get(class_id, class_id))
        if isinstance(self._model_names, list) and 0 <= class_id < len(self._model_names):
            return str(self._model_names[class_id])
        return str(class_id)


class EnsembleBackend(InferenceBackend):
    """Combina previsoes de multiplos YOLOs (ex.: best_v1 + best_v2) por consenso."""

    def __init__(self, runtime: RuntimeConfig) -> None:
        self.runtime = runtime
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                "Ultralytics nao esta instalado. Rode `pip install -e .` no projeto."
            ) from exc

        paths = list(runtime.model_paths) if runtime.model_paths else []
        if not paths and runtime.model_path:
            paths = [runtime.model_path]
        if len(paths) < 2:
            # Fallback automatico para os pesos do Colab se existirem
            root = Path(runtime.model_path).resolve().parent if runtime.model_path else Path("models")
            for name in ("best_v1.pt", "best_v2.pt"):
                candidate = root / name
                if candidate.is_file() and str(candidate) not in paths:
                    paths.append(str(candidate))
        if not paths:
            raise RuntimeError(
                "Ensemble sem modelos. Configure model_paths: [models/best_v1.pt, models/best_v2.pt]"
            )

        self.models = []
        self._model_names = None
        for path in paths:
            if not Path(path).is_file():
                raise RuntimeError(f"Peso do ensemble nao encontrado: {path}")
            model = YOLO(path)
            self.models.append(model)
            self._model_names = model.names
        logger.info("Ensemble ativo com %s modelos: %s", len(self.models), paths)

    def detect(self, frame: np.ndarray) -> list[Detection]:
        per_model: list[list[Detection]] = []
        for model in self.models:
            results = model.predict(
                source=frame,
                conf=max(0.15, self.runtime.confidence * 0.7),
                iou=self.runtime.iou,
                verbose=False,
            )
            detections: list[Detection] = []
            for result in results:
                boxes = getattr(result, "boxes", None)
                if boxes is None:
                    continue
                for box in boxes:
                    class_id = int(box.cls[0].item())
                    label = self._resolve_label(class_id)
                    if self.runtime.target_label and not _labels_match(
                        label, self.runtime.target_label
                    ):
                        continue
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    detections.append(
                        Detection(
                            bbox=(int(x1), int(y1), int(x2), int(y2)),
                            confidence=float(box.conf[0].item()),
                            label=label,
                        )
                    )
            per_model.append(detections)

        return _consensus_merge(
            per_model,
            iou_threshold=self.runtime.ensemble_iou,
            solo_confidence=self.runtime.ensemble_solo_confidence,
        )

    def _resolve_label(self, class_id: int) -> str:
        if isinstance(self._model_names, dict):
            return str(self._model_names.get(class_id, class_id))
        if isinstance(self._model_names, list) and 0 <= class_id < len(self._model_names):
            return str(self._model_names[class_id])
        return str(class_id)


def _consensus_merge(
    per_model: list[list[Detection]],
    *,
    iou_threshold: float,
    solo_confidence: float,
) -> list[Detection]:
    """Mantem boxes com consenso (>=2 modelos) ou confianca solo alta."""
    tagged: list[tuple[int, Detection]] = []
    for model_idx, detections in enumerate(per_model):
        for det in detections:
            tagged.append((model_idx, det))
    tagged.sort(key=lambda item: item[1].confidence, reverse=True)

    used = [False] * len(tagged)
    merged: list[Detection] = []
    for index, (model_idx, seed) in enumerate(tagged):
        if used[index]:
            continue
        cluster = [(model_idx, seed)]
        used[index] = True
        voters = {model_idx}
        for other_index in range(index + 1, len(tagged)):
            if used[other_index]:
                continue
            other_model, other = tagged[other_index]
            if other.label != seed.label:
                continue
            if _bbox_overlap_ratio(seed.bbox, other.bbox) < iou_threshold:
                continue
            used[other_index] = True
            cluster.append((other_model, other))
            voters.add(other_model)

        max_conf = max(det.confidence for _, det in cluster)
        if len(voters) < 2 and max_conf < solo_confidence:
            continue

        xs1 = [det.bbox[0] for _, det in cluster]
        ys1 = [det.bbox[1] for _, det in cluster]
        xs2 = [det.bbox[2] for _, det in cluster]
        ys2 = [det.bbox[3] for _, det in cluster]
        confs = [det.confidence for _, det in cluster]
        # Consenso: media ponderada pela confianca
        weight = sum(confs) or 1.0
        bbox = (
            int(round(sum(x * c for x, c in zip(xs1, confs)) / weight)),
            int(round(sum(y * c for y, c in zip(ys1, confs)) / weight)),
            int(round(sum(x * c for x, c in zip(xs2, confs)) / weight)),
            int(round(sum(y * c for y, c in zip(ys2, confs)) / weight)),
        )
        boost = 1.0 + (0.08 * max(0, len(voters) - 1))
        merged.append(
            Detection(
                bbox=bbox,
                confidence=min(0.99, max_conf * boost),
                label=seed.label,
            )
        )
    return merged


def _labels_match(label: str, target: str) -> bool:
    aliases = {
        "egg": {"egg", "ovo", "eggs"},
        "ovo": {"egg", "ovo", "eggs"},
    }
    normalized = label.lower().strip()
    wanted = target.lower().strip()
    return normalized == wanted or normalized in aliases.get(wanted, set())


class RoboflowBackend(InferenceBackend):
    """Detecta ovos via Roboflow RAPID (API na nuvem)."""

    def __init__(self, runtime: RuntimeConfig) -> None:
        if not runtime.roboflow_api_key:
            raise RuntimeError(
                "ROBOFLOW_API_KEY nao configurada. "
                "Crie python/egg/.env com ROBOFLOW_API_KEY=..."
            )
        if not runtime.roboflow_workspace or not runtime.roboflow_workflow_id:
            raise RuntimeError(
                "Configure roboflow_workspace e roboflow_workflow_id no runtime.yaml "
                "ou via ROBOFLOW_WORKSPACE / ROBOFLOW_WORKFLOW_ID."
            )

        try:
            from inference_sdk import InferenceHTTPClient
        except ImportError as exc:
            raise RuntimeError(
                "inference-sdk nao esta instalado. Rode: pip install inference-sdk"
            ) from exc

        self.runtime = runtime
        self.workspace = runtime.roboflow_workspace
        self.workflow_id = runtime.roboflow_workflow_id
        self.client = InferenceHTTPClient(
            api_url=runtime.roboflow_api_url,
            api_key=runtime.roboflow_api_key,
        )
        logger.info(
            "Roboflow backend ativo: workspace=%s workflow=%s",
            self.workspace,
            self.workflow_id,
        )

    def detect(self, frame: np.ndarray) -> list[Detection]:
        ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ok:
            logger.warning("Falha ao codificar frame para Roboflow")
            return []

        tmp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as handle:
                handle.write(encoded.tobytes())
                tmp_path = Path(handle.name)
            try:
                result = self.client.run_workflow(
                    workspace_name=self.workspace,
                    workflow_id=self.workflow_id,
                    images={"image": str(tmp_path)},
                    use_cache=True,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Roboflow inferencia falhou: %s", exc)
                return []
            return self._parse_result(result)
        finally:
            if tmp_path is not None:
                tmp_path.unlink(missing_ok=True)

    def _parse_result(self, result: Any) -> list[Detection]:
        predictions = _extract_roboflow_predictions(result)
        detections: list[Detection] = []
        for item in predictions:
            if not isinstance(item, dict):
                continue
            label = str(item.get("class") or item.get("label") or "egg")
            if self.runtime.target_label and not _labels_match(label, self.runtime.target_label):
                continue
            confidence = float(item.get("confidence", 0.0))
            if confidence < self.runtime.confidence:
                continue
            bbox = _roboflow_item_to_xyxy(item)
            if bbox is None:
                continue
            detections.append(Detection(bbox=bbox, confidence=confidence, label=label))
        return detections


def _extract_roboflow_predictions(result: Any) -> list[dict[str, Any]]:
    """Normaliza respostas do run_workflow / infer para lista de predicoes."""
    if result is None:
        return []

    payloads: list[Any] = result if isinstance(result, list) else [result]
    collected: list[dict[str, Any]] = []
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        preds = payload.get("predictions", payload)
        if isinstance(preds, dict):
            inner = preds.get("predictions", [])
            if isinstance(inner, list):
                collected.extend(item for item in inner if isinstance(item, dict))
            continue
        if isinstance(preds, list):
            collected.extend(item for item in preds if isinstance(item, dict))
    return collected


def _roboflow_item_to_xyxy(item: dict[str, Any]) -> tuple[int, int, int, int] | None:
    """Converte predicao Roboflow (centro x/y + w/h) para bbox xyxy."""
    if all(k in item for k in ("x1", "y1", "x2", "y2")):
        return (
            int(item["x1"]),
            int(item["y1"]),
            int(item["x2"]),
            int(item["y2"]),
        )
    if all(k in item for k in ("x", "y", "width", "height")):
        cx = float(item["x"])
        cy = float(item["y"])
        width = float(item["width"])
        height = float(item["height"])
        x1 = int(round(cx - width / 2.0))
        y1 = int(round(cy - height / 2.0))
        x2 = int(round(cx + width / 2.0))
        y2 = int(round(cy + height / 2.0))
        return (x1, y1, x2, y2)
    return None


class ClassicBackend(InferenceBackend):
    """Detecta ovos ovais na esteira e ignora buracos circulares."""

    def __init__(self, runtime: RuntimeConfig) -> None:
        self.diff_threshold = runtime.diff_threshold
        self._reference_gray: np.ndarray | None = None
        self._reference_by_size: dict[tuple[int, int], np.ndarray] = {}
        self._clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        self._frame_cache: _FrameCache | None = None

        if runtime.reference_image:
            reference_path = Path(runtime.reference_image)
            if reference_path.exists():
                reference = cv2.imread(str(reference_path))
                if reference is not None:
                    self._reference_gray = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)
                else:
                    logger.warning(
                        "Nao foi possivel ler a imagem de referencia: %s",
                        reference_path,
                    )
            else:
                logger.warning(
                    "Imagem de referencia nao encontrada: %s. "
                    "A deteccao classic usara apenas contornos elipticos.",
                    reference_path,
                )

    def detect(self, frame: np.ndarray) -> list[Detection]:
        height, width = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hole_radius = self._estimate_hole_radius_from_gray(gray)
        reference = self._get_reference_gray(width, height)
        reference_aligned = (
            reference is not None and float(cv2.absdiff(gray, reference).mean()) <= 30.0
        )
        self._frame_cache = _FrameCache(
            gray=gray,
            hsv=hsv,
            hole_radius=hole_radius,
            frame_hole_score=self._hole_regularity_score(gray, hole_radius),
            reference=reference,
            reference_aligned=reference_aligned,
        )

        try:
            candidates: list[tuple[tuple[int, int, int, int], float, float]] = []
            reference_candidates: list[tuple[tuple[int, int, int, int], float, float]] = []
            if reference is not None:
                reference_candidates = self._detect_by_reference_diff(frame, hole_radius)

            if reference_aligned:
                candidates = reference_candidates
                if len(candidates) < 2:
                    candidates.extend(self._detect_by_low_contrast_egg(frame, hole_radius))
            else:
                candidates.extend(reference_candidates)
                candidates.extend(self._detect_by_ellipse(frame, hole_radius))
                candidates.extend(self._detect_by_brown_egg_color(frame, hole_radius))
                if len(candidates) < 2:
                    candidates.extend(self._detect_by_low_contrast_egg(frame, hole_radius))

            validated = [
                candidate
                for candidate in candidates
                if self._is_valid_egg_candidate(frame, candidate[0], hole_radius)
            ]
            merged = self._merge_candidates(validated, hole_radius)

            detections: list[Detection] = []
            for bbox, confidence in merged:
                detections.append(
                    Detection(
                        bbox=bbox,
                        confidence=confidence,
                        label="egg",
                    )
                )
            return detections
        finally:
            self._frame_cache = None

    def _get_reference_gray(self, width: int, height: int) -> np.ndarray | None:
        if self._reference_gray is None:
            return None
        key = (width, height)
        cached = self._reference_by_size.get(key)
        if cached is None:
            cached = cv2.resize(
                self._reference_gray,
                (width, height),
                interpolation=cv2.INTER_LINEAR,
            )
            self._reference_by_size[key] = cached
        return cached

    def _is_reference_aligned(self, frame: np.ndarray) -> bool:
        if self._frame_cache is not None:
            return self._frame_cache.reference_aligned
        if self._reference_gray is None:
            return False

        height, width = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        reference = self._get_reference_gray(width, height)
        if reference is None:
            return False
        return float(cv2.absdiff(gray, reference).mean()) <= 30.0

    def _estimate_hole_radius(self, frame: np.ndarray) -> float:
        if self._frame_cache is not None:
            return self._frame_cache.hole_radius
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return self._estimate_hole_radius_from_gray(gray)

    def _estimate_hole_radius_from_gray(self, gray: np.ndarray) -> float:
        blur = cv2.GaussianBlur(gray, (9, 9), 2)
        circles = cv2.HoughCircles(
            blur,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=20,
            param1=60,
            param2=18,
            minRadius=6,
            maxRadius=26,
        )
        if circles is None:
            return 12.5
        return float(np.median(circles[0, :, 2]))

    def _hole_diameter(self, hole_radius: float) -> float:
        return max(18.0, hole_radius * 2.0)

    def _min_egg_dimension(self, hole_radius: float) -> float:
        """Ovo precisa ser visivelmente maior que o furo da esteira."""
        return self._hole_diameter(hole_radius) * 1.55

    def _is_egg_sized_bbox(
        self,
        bbox: tuple[int, int, int, int],
        hole_radius: float,
    ) -> bool:
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        if width <= 0 or height <= 0:
            return False

        hole_diameter = self._hole_diameter(hole_radius)
        min_required = self._min_egg_dimension(hole_radius)
        short_side = min(width, height)
        long_side = max(width, height)
        return short_side >= min_required and long_side >= hole_diameter * 1.65

    def _detect_by_reference_diff(
        self,
        frame: np.ndarray,
        hole_radius: float,
    ) -> list[tuple[tuple[int, int, int, int], float, float]]:
        if self._reference_gray is None:
            return []

        cache = self._frame_cache
        if cache is not None and cache.reference is not None:
            gray = cache.gray
            hsv = cache.hsv
            reference = cache.reference
        else:
            height, width = frame.shape[:2]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            reference = self._get_reference_gray(width, height)
            if reference is None:
                return []

        height, width = gray.shape[:2]
        diff = cv2.absdiff(gray, reference)
        saturation = hsv[:, :, 1]
        value = hsv[:, :, 2]
        diff_threshold = max(10.0, self.diff_threshold * 0.22)
        color_mask = (saturation > 38) | ((saturation < 75) & (value > 130) & (gray > 120))
        mask = (
            (diff > diff_threshold)
            & color_mask
            & (gray > 90)
        ).astype(np.uint8) * 255
        mask = self._remove_overlay_artifacts(frame, mask)

        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (max(5, int(hole_radius * 1.1)) | 1, max(7, int(hole_radius * 1.9)) | 1),
        )
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask = cv2.morphologyEx(
            mask,
            cv2.MORPH_OPEN,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
        )

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates: list[tuple[tuple[int, int, int, int], float, float]] = []
        min_area = max(
            900.0,
            np.pi * (self._min_egg_dimension(hole_radius) / 2.0) ** 2,
        )
        min_box_width = int(self._min_egg_dimension(hole_radius))
        min_box_height = int(self._hole_diameter(hole_radius) * 1.35)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue

            x, y, box_width, box_height = cv2.boundingRect(contour)
            if box_width < min_box_width or box_height < min_box_height:
                continue
            if box_width > width * 0.45 or box_height > height * 0.55:
                continue
            if x < 3 or x + box_width > width - 3:
                continue

            diff_roi = diff[y : y + box_height, x : x + box_width]
            gray_roi = gray[y : y + box_height, x : x + box_width]
            sat_roi = saturation[y : y + box_height, x : x + box_width]
            sat_mean = float(sat_roi.mean())
            gray_mean = float(gray_roi.mean())
            is_white_region = sat_mean < 75 and gray_mean > 125
            min_diff = 12.0 if is_white_region else 24.0
            min_diff_ratio = 0.22 if is_white_region else 0.38
            if float(diff_roi.mean()) < min_diff or float((diff_roi > 12).mean()) < min_diff_ratio:
                continue
            if not is_white_region and sat_mean < 35.0:
                continue

            confidence = min(0.99, 0.7 + float(diff_roi.mean()) / 200.0)
            candidates.append(
                (
                    (x, y, x + box_width, y + box_height),
                    confidence,
                    float(box_width * box_height),
                )
            )

        return candidates

    def _detect_by_low_contrast_egg(
        self,
        frame: np.ndarray,
        hole_radius: float,
    ) -> list[tuple[tuple[int, int, int, int], float, float]]:
        cache = self._frame_cache
        if cache is not None:
            gray = cache.gray
            hsv = cache.hsv
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        height, width = gray.shape[:2]
        saturation = hsv[:, :, 1]

        enhanced = self._clahe.apply(gray)
        blur = cv2.GaussianBlur(enhanced, (7, 7), 0)
        edges = cv2.Canny(blur, 28, 75)
        edges = cv2.dilate(
            edges,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)),
            iterations=1,
        )

        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        margin = 12
        min_axis = self._min_egg_dimension(hole_radius)
        max_axis = hole_radius * 9.0
        candidates: list[tuple[tuple[int, int, int, int], float, float]] = []

        for contour in contours:
            if len(contour) < 12:
                continue

            area = cv2.contourArea(contour)
            min_area = max(700.0, np.pi * (self._min_egg_dimension(hole_radius) / 2.2) ** 2)
            if area < min_area or area > 4200:
                continue

            try:
                (_, _), (major_axis, minor_axis), _ = cv2.fitEllipse(contour)
            except cv2.error:
                continue

            short_axis = min(major_axis, minor_axis)
            long_axis = max(major_axis, minor_axis)
            if short_axis < min_axis or long_axis > max_axis:
                continue

            aspect_ratio = long_axis / max(1.0, short_axis)
            if aspect_ratio < 1.15 or aspect_ratio > 2.2:
                continue

            x, y, box_width, box_height = cv2.boundingRect(contour)
            if not self._is_egg_sized_bbox((x, y, x + box_width, y + box_height), hole_radius):
                continue
            if (
                x < margin
                or y < margin
                or x + box_width > width - margin
                or y + box_height > height - margin
            ):
                continue
            if box_height > height * 0.4 or box_width > width * 0.22:
                continue

            roi_gray = gray[y : y + box_height, x : x + box_width]
            roi_sat = saturation[y : y + box_height, x : x + box_width]
            gray_mean = float(roi_gray.mean())
            sat_mean = float(roi_sat.mean())
            if gray_mean < 138 or sat_mean > 80:
                continue

            confidence = min(0.9, 0.58 + aspect_ratio * 0.05 + min(area, 2200) / 6000)
            candidates.append(
                (
                    (x, y, x + box_width, y + box_height),
                    confidence,
                    float(box_width * box_height),
                )
            )

        return candidates

    def _detect_by_ellipse(
        self,
        frame: np.ndarray,
        hole_radius: float,
    ) -> list[tuple[tuple[int, int, int, int], float, float]]:
        cache = self._frame_cache
        gray = cache.gray if cache is not None else cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape[:2]
        blur = cv2.GaussianBlur(gray, (9, 9), 2)
        edges = cv2.Canny(blur, 40, 120)
        edges = cv2.dilate(
            edges,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)),
            iterations=1,
        )

        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        margin = 20
        min_axis = self._min_egg_dimension(hole_radius)
        max_axis = hole_radius * 10.0
        candidates: list[tuple[tuple[int, int, int, int], float, float]] = []

        for contour in contours:
            if len(contour) < 20:
                continue

            area = cv2.contourArea(contour)
            min_area = max(650.0, np.pi * (self._min_egg_dimension(hole_radius) / 2.0) ** 2)
            if area < min_area or area > 12000:
                continue

            try:
                (center_x, center_y), (major_axis, minor_axis), _ = cv2.fitEllipse(contour)
            except cv2.error:
                continue

            short_axis = min(major_axis, minor_axis)
            long_axis = max(major_axis, minor_axis)
            if short_axis < min_axis or long_axis > max_axis:
                continue

            aspect_ratio = long_axis / max(1.0, short_axis)
            if aspect_ratio < 1.12 or aspect_ratio > 2.8:
                continue

            x1 = int(center_x - major_axis / 2 - 4)
            y1 = int(center_y - minor_axis / 2 - 4)
            x2 = int(center_x + major_axis / 2 + 4)
            y2 = int(center_y + minor_axis / 2 + 4)
            if not self._is_egg_sized_bbox((x1, y1, x2, y2), hole_radius):
                continue
            if x1 < margin or y1 < margin or x2 > width - margin or y2 > height - margin:
                continue

            roi = gray[max(0, y1) : min(height, y2), max(0, x1) : min(width, x2)]
            if roi.size == 0 or float(roi.mean()) < 95:
                continue

            confidence = min(
                0.95,
                0.65 + (aspect_ratio - 1.0) * 0.08 + min(area, 2500) / 5000,
            )
            candidates.append(((x1, y1, x2, y2), confidence, area))

        return candidates

    def _detect_by_brown_egg_color(
        self,
        frame: np.ndarray,
        hole_radius: float,
    ) -> list[tuple[tuple[int, int, int, int], float, float]]:
        cache = self._frame_cache
        if cache is not None:
            hsv = cache.hsv
            gray = cache.gray
        else:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape[:2]
        color_mask = (
            (hsv[:, :, 0] >= 5)
            & (hsv[:, :, 0] <= 62)
            & (hsv[:, :, 1] >= 18)
            & (hsv[:, :, 2] >= 85)
            & (gray > 95)
        ).astype(np.uint8) * 255
        color_mask = cv2.morphologyEx(
            color_mask,
            cv2.MORPH_OPEN,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)),
        )
        color_mask = cv2.morphologyEx(
            color_mask,
            cv2.MORPH_CLOSE,
            cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE,
                (max(5, int(hole_radius * 0.7)) | 1, max(7, int(hole_radius * 1.1)) | 1),
            ),
            iterations=1,
        )

        # Mild erode keeps touching eggs separable
        lane_mask = color_mask.copy()
        lane_mask = cv2.erode(
            lane_mask,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)),
            iterations=1,
        )
        candidates = self._collect_brown_candidates(
            lane_mask,
            hole_radius,
            gray,
            hsv,
            height,
            width,
            x_offset=0,
        )
        return candidates

    def _detect_brown_by_distance_peaks(
        self,
        color_mask: np.ndarray,
        hole_radius: float,
        gray: np.ndarray,
        hsv: np.ndarray,
    ) -> list[tuple[tuple[int, int, int, int], float, float]]:
        """Split crowded brown eggs using distance-transform local maxima."""
        if color_mask.size == 0 or int(cv2.countNonZero(color_mask)) < 200:
            return []

        dist = cv2.distanceTransform(color_mask, cv2.DIST_L2, 5)
        typical = self._min_egg_dimension(hole_radius)
        min_peak = max(4.0, typical * 0.22)
        kernel = max(9, int(typical * 0.85)) | 1
        dilated = cv2.dilate(dist, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel, kernel)))
        peaks = (dist >= dilated) & (dist >= min_peak) & (color_mask > 0)
        peak_points = np.column_stack(np.where(peaks))
        if peak_points.size == 0:
            return []

        # Keep spatially separated peaks
        selected: list[tuple[int, int, float]] = []
        min_sep = max(18.0, typical * 0.55)
        for y, x in sorted(peak_points, key=lambda p: float(dist[p[0], p[1]]), reverse=True):
            if any((x - sx) ** 2 + (y - sy) ** 2 < min_sep**2 for sy, sx, _ in selected):
                continue
            selected.append((int(y), int(x), float(dist[y, x])))
            if len(selected) >= 20:
                break

        height, width = gray.shape[:2]
        half = max(14, int(typical * 0.72))
        candidates: list[tuple[tuple[int, int, int, int], float, float]] = []
        for y, x, radius in selected:
            x1 = max(0, x - half)
            y1 = max(0, y - half)
            x2 = min(width, x + half)
            y2 = min(height, y + half)
            area = float((x2 - x1) * (y2 - y1) * 0.55)
            candidate = self._brown_bbox_candidate(
                (x1, y1, x2, y2),
                area,
                hole_radius,
                gray,
                hsv,
                width,
                height,
            )
            if candidate is not None:
                candidates.append(candidate)
        return candidates

    def _collect_brown_candidates(
        self,
        color_mask: np.ndarray,
        hole_radius: float,
        gray: np.ndarray,
        hsv: np.ndarray,
        height: int,
        width: int,
        x_offset: int,
    ) -> list[tuple[tuple[int, int, int, int], float, float]]:
        contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates: list[tuple[tuple[int, int, int, int], float, float]] = []
        min_area = max(900.0, np.pi * (self._min_egg_dimension(hole_radius) / 2.0) ** 2)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue

            x, y, box_width, box_height = cv2.boundingRect(contour)
            bbox = (x_offset + x, y, x_offset + x + box_width, y + box_height)
            typical_egg = self._min_egg_dimension(hole_radius)
            too_wide = box_width > max(width * 0.18, typical_egg * 1.55)
            too_tall = box_height > max(height * 0.32, typical_egg * 1.7)
            too_large = area > max(min_area * 1.7, np.pi * (typical_egg * 0.75) ** 2 * 1.8)
            if too_wide or too_tall or too_large:
                candidates.extend(
                    self._split_brown_blob_candidates(
                        color_mask,
                        (x, y, x + box_width, y + box_height),
                        hole_radius,
                        gray,
                        hsv,
                        min_area,
                        x_offset=x_offset,
                    )
                )
                continue

            candidate = self._brown_bbox_candidate(
                bbox,
                area,
                hole_radius,
                gray,
                hsv,
                width,
                height,
            )
            if candidate is not None:
                candidates.append(candidate)

        return candidates

    def _split_brown_blob_candidates(
        self,
        color_mask: np.ndarray,
        bbox: tuple[int, int, int, int],
        hole_radius: float,
        gray: np.ndarray,
        hsv: np.ndarray,
        min_area: float,
        x_offset: int = 0,
    ) -> list[tuple[tuple[int, int, int, int], float, float]]:
        x1, y1, x2, y2 = bbox
        roi_mask = color_mask[y1:y2, x1:x2]
        if roi_mask.size == 0:
            return []

        dist = cv2.distanceTransform(roi_mask, cv2.DIST_L2, 5)
        candidates: list[tuple[tuple[int, int, int, int], float, float]] = []
        frame_height, frame_width = gray.shape[:2]
        typical_egg = self._min_egg_dimension(hole_radius)

        if float(dist.max()) > 0:
            # Lower threshold separates touching eggs
            _, sure_fg = cv2.threshold(dist, 0.28 * float(dist.max()), 255, 0)
            sure_fg = sure_fg.astype(np.uint8)
            sure_fg = cv2.erode(
                sure_fg,
                cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)),
                iterations=1,
            )
            # Watershed markers from local maxima
            unknown = cv2.subtract(roi_mask, sure_fg)
            _, markers = cv2.connectedComponents(sure_fg)
            markers = markers + 1
            markers[unknown == 255] = 0
            color_roi = cv2.cvtColor(roi_mask, cv2.COLOR_GRAY2BGR)
            cv2.watershed(color_roi, markers)

            labels = [int(value) for value in np.unique(markers) if int(value) > 1]
            for label in labels:
                component = np.zeros_like(roi_mask)
                component[markers == label] = 255
                sub_contours, _ = cv2.findContours(
                    component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )
                for contour in sub_contours:
                    area = cv2.contourArea(contour)
                    if area < min_area * 0.45:
                        continue
                    sx, sy, sw, sh = cv2.boundingRect(contour)
                    sub_bbox = (
                        x_offset + x1 + sx,
                        y1 + sy,
                        x_offset + x1 + sx + sw,
                        y1 + sy + sh,
                    )
                    candidate = self._brown_bbox_candidate(
                        sub_bbox,
                        area,
                        hole_radius,
                        gray,
                        hsv,
                        frame_width,
                        frame_height,
                    )
                    if candidate is not None:
                        candidates.append(candidate)

            if len(candidates) < 2:
                sub_contours, _ = cv2.findContours(
                    sure_fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )
                for contour in sub_contours:
                    area = cv2.contourArea(contour)
                    if area < min_area * 0.45:
                        continue
                    sx, sy, sw, sh = cv2.boundingRect(contour)
                    sub_bbox = (
                        x_offset + x1 + sx,
                        y1 + sy,
                        x_offset + x1 + sx + sw,
                        y1 + sy + sh,
                    )
                    candidate = self._brown_bbox_candidate(
                        sub_bbox,
                        area,
                        hole_radius,
                        gray,
                        hsv,
                        frame_width,
                        frame_height,
                    )
                    if candidate is not None:
                        candidates.append(candidate)

        candidates = self._dedupe_split_candidates(candidates)

        # Geometric split for side-by-side / stacked touching eggs
        box_w = x2 - x1
        box_h = y2 - y1
        if len(candidates) < 2 and box_w >= typical_egg * 1.45:
            mid_x = (x1 + x2) // 2
            for sub_bbox in (
                (x_offset + x1, y1, x_offset + mid_x, y2),
                (x_offset + mid_x, y1, x_offset + x2, y2),
            ):
                sub_area = float((sub_bbox[2] - sub_bbox[0]) * (sub_bbox[3] - sub_bbox[1]) * 0.55)
                candidate = self._brown_bbox_candidate(
                    sub_bbox,
                    sub_area,
                    hole_radius,
                    gray,
                    hsv,
                    frame_width,
                    frame_height,
                )
                if candidate is not None:
                    candidates.append(candidate)

        if len(candidates) < 2 and box_h >= typical_egg * 1.6:
            mid_y = (y1 + y2) // 2
            for sub_bbox in (
                (x_offset + x1, y1, x_offset + x2, mid_y),
                (x_offset + x1, mid_y, x_offset + x2, y2),
            ):
                sub_area = float((sub_bbox[2] - sub_bbox[0]) * (sub_bbox[3] - sub_bbox[1]) * 0.55)
                candidate = self._brown_bbox_candidate(
                    sub_bbox,
                    sub_area,
                    hole_radius,
                    gray,
                    hsv,
                    frame_width,
                    frame_height,
                )
                if candidate is not None:
                    candidates.append(candidate)

        candidates = self._dedupe_split_candidates(candidates)
        if candidates:
            return candidates

        # Last resort: keep original bbox if it looks like a single egg
        original = self._brown_bbox_candidate(
            (x_offset + x1, y1, x_offset + x2, y2),
            float((x2 - x1) * (y2 - y1) * 0.55),
            hole_radius,
            gray,
            hsv,
            frame_width,
            frame_height,
        )
        return [original] if original is not None else []

    def _dedupe_split_candidates(
        self,
        candidates: list[tuple[tuple[int, int, int, int], float, float]],
    ) -> list[tuple[tuple[int, int, int, int], float, float]]:
        """Drop nested/duplicate boxes from watershed (keep the smaller distinct eggs)."""
        ordered = sorted(candidates, key=lambda item: item[2])  # smaller area first
        kept: list[tuple[tuple[int, int, int, int], float, float]] = []
        for candidate in ordered:
            bbox = candidate[0]
            # Skip if almost fully contained in an already kept box or vice-versa
            redundant = False
            for other in kept:
                overlap = _bbox_overlap_ratio(bbox, other[0])
                if overlap >= 0.55:
                    redundant = True
                    break
            if not redundant:
                kept.append(candidate)
        return kept

    def _brown_bbox_candidate(
        self,
        bbox: tuple[int, int, int, int],
        area: float,
        hole_radius: float,
        gray: np.ndarray,
        hsv: np.ndarray,
        width: int,
        height: int,
    ) -> tuple[tuple[int, int, int, int], float, float] | None:
        x1, y1, x2, y2 = bbox
        box_width = x2 - x1
        box_height = y2 - y1
        if not self._is_egg_sized_bbox(bbox, hole_radius):
            return None
        if box_width > width * 0.28 or box_height > height * 0.45:
            return None
        # Reject edge artifacts (belt corners / UI crop)
        if x1 <= 2 or y1 <= 2 or x2 >= width - 2:
            return None

        roi_gray = gray[y1:y2, x1:x2]
        roi_hsv = hsv[y1:y2, x1:x2]
        if not self._has_egg_color_signature(roi_gray, roi_hsv):
            return None

        aspect = box_width / max(1.0, box_height)
        if aspect < 0.45 or aspect > 2.1:
            return None

        confidence = min(0.94, 0.72 + min(area, 3200) / 5000)
        return (bbox, confidence, float(box_width * box_height))

    def _has_egg_color_signature(
        self,
        roi_gray: np.ndarray,
        roi_hsv: np.ndarray,
    ) -> bool:
        gray_mean = float(roi_gray.mean())
        saturation_mean = float(roi_hsv[:, :, 1].mean())
        hue_mean = float(roi_hsv[:, :, 0].mean())
        is_white_egg = saturation_mean < 75 and gray_mean > 140
        is_brown_egg = 5 <= hue_mean <= 62 and saturation_mean >= 18 and 95 < gray_mean < 210
        return is_white_egg or is_brown_egg

    def _merge_candidates(
        self,
        candidates: list[tuple[tuple[int, int, int, int], float, float]],
        hole_radius: float,
    ) -> list[tuple[tuple[int, int, int, int], float]]:
        kept: list[tuple[tuple[int, int, int, int], float, float, float, float]] = []
        # Distancia menor evita fundir ovos vizinhos na mesma fileira
        min_distance = max(28.0, hole_radius * 2.2)

        for bbox, confidence, score in sorted(candidates, key=lambda item: item[2], reverse=True):
            center_x = (bbox[0] + bbox[2]) / 2
            center_y = (bbox[1] + bbox[3]) / 2
            if any(
                (
                    (center_x - other_center_x) ** 2 + (center_y - other_center_y) ** 2
                    <= min_distance**2
                )
                or _bbox_overlap_ratio(bbox, other_bbox) >= 0.55
                for other_bbox, _, _, other_center_x, other_center_y in kept
            ):
                continue
            kept.append((bbox, confidence, score, center_x, center_y))

        return [(bbox, confidence) for bbox, confidence, _, _, _ in kept]

    def _remove_overlay_artifacts(self, frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
        cache = self._frame_cache
        if cache is not None:
            hsv = cache.hsv
        else:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        overlay = cv2.bitwise_or(
            cv2.inRange(hsv, (35, 80, 80), (85, 255, 255)),
            cv2.inRange(hsv, (90, 80, 80), (130, 255, 255)),
        )
        return cv2.bitwise_and(mask, cv2.bitwise_not(overlay))

    def _is_valid_egg_candidate(
        self,
        frame: np.ndarray,
        bbox: tuple[int, int, int, int],
        hole_radius: float,
    ) -> bool:
        if not self._is_egg_sized_bbox(bbox, hole_radius):
            return False
        if self._is_hollow_belt_hole(frame, bbox, hole_radius):
            return False
        if self._looks_like_belt_hole(frame, bbox, hole_radius):
            return False
        if not self._has_solid_egg_fill(frame, bbox):
            return False

        if self._passes_brown_egg_shape(frame, bbox, hole_radius):
            return True
        if self._passes_low_contrast_egg_shape(frame, bbox, hole_radius):
            return True
        if self._is_on_irregular_belt(frame, bbox, hole_radius):
            return False
        return self._is_filled_egg_blob(frame, bbox, hole_radius)

    def _has_solid_egg_fill(
        self,
        frame: np.ndarray,
        bbox: tuple[int, int, int, int],
    ) -> bool:
        """Eggs are filled (center not darker than the belt hole pattern)."""
        x1, y1, x2, y2 = bbox
        roi_gray = cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
        height, width = roi_gray.shape
        if height < 10 or width < 10:
            return False

        margin_y = max(2, height // 5)
        margin_x = max(2, width // 5)
        center = roi_gray[margin_y:-margin_y, margin_x:-margin_x]
        border_mask = np.ones(roi_gray.shape, dtype=np.uint8)
        border_mask[margin_y:-margin_y, margin_x:-margin_x] = 0
        border = roi_gray[border_mask == 1]
        if center.size == 0 or border.size == 0:
            return False

        center_mean = float(center.mean())
        border_mean = float(border.mean())
        center_std = float(center.std())
        # Belt holes: dark center, brighter rim
        if center_mean < border_mean - 12.0:
            return False
        if center_mean < 105.0:
            return False
        # Perforated belt patch: many dark pixels + high local variance
        dark_ratio = float((center < 115).mean())
        if dark_ratio > 0.14 and center_std > 22.0:
            return False
        if dark_ratio > 0.18:
            return False
        return True

    def _is_perforated_belt_patch(self, frame: np.ndarray, bbox: tuple[int, int, int, int]) -> bool:
        """True when the box covers empty belt with multiple dark holes."""
        x1, y1, x2, y2 = bbox
        roi = cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
        if roi.size == 0 or min(roi.shape) < 16:
            return False
        blur = cv2.GaussianBlur(roi, (5, 5), 1)
        _, dark = cv2.threshold(blur, 115, 255, cv2.THRESH_BINARY_INV)
        dark = cv2.morphologyEx(
            dark,
            cv2.MORPH_OPEN,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)),
        )
        contours, _ = cv2.findContours(dark, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        hole_like = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 25 or area > 900:
                continue
            bx, by, bw, bh = cv2.boundingRect(contour)
            aspect = bw / max(1.0, bh)
            if 0.65 <= aspect <= 1.45:
                hole_like += 1
        # Empty belt patches usually contain several perforations
        return hole_like >= 2

    def _has_egg_body_color(self, frame: np.ndarray, bbox: tuple[int, int, int, int]) -> bool:
        """Reject empty belt patches that look bright but lack egg chroma."""
        if self._is_perforated_belt_patch(frame, bbox):
            return False
        x1, y1, x2, y2 = bbox
        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return False
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        h, w = gray.shape
        cy1, cy2 = h // 4, 3 * h // 4
        cx1, cx2 = w // 4, 3 * w // 4
        center_gray = gray[cy1:cy2, cx1:cx2]
        center_hsv = hsv[cy1:cy2, cx1:cx2]
        if center_gray.size == 0:
            return False
        gray_mean = float(center_gray.mean())
        gray_std = float(center_gray.std())
        sat_mean = float(center_hsv[:, :, 1].mean())
        hue_mean = float(center_hsv[:, :, 0].mean())
        dark_ratio = float((center_gray < 115).mean())
        if dark_ratio > 0.16:
            return False
        # Brown / beige eggs on this belt
        if 5 <= hue_mean <= 62 and sat_mean >= 28 and 105 < gray_mean < 200 and gray_std < 36.0:
            return True
        # White eggs: bright, uniform, not empty belt glare / hole grid
        if (
            sat_mean < 55
            and 155 < gray_mean < 205
            and gray_std < 18.0
            and sat_mean >= 10.0
            and dark_ratio < 0.08
        ):
            return True
        return False

    def _looks_like_belt_hole(
        self,
        frame: np.ndarray,
        bbox: tuple[int, int, int, int],
        hole_radius: float,
    ) -> bool:
        """Reject circular dark openings that match belt perforation size."""
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        short_side = min(width, height)
        long_side = max(width, height)
        hole_diameter = self._hole_diameter(hole_radius)

        # Typical belt hole size band
        if short_side > hole_diameter * 2.8:
            return False

        aspect = width / max(1.0, height)
        if aspect < 0.75 or aspect > 1.35:
            return False

        roi_gray = cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
        roi_hsv = cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2HSV)
        center = roi_gray[height // 4 : 3 * height // 4, width // 4 : 3 * width // 4]
        if center.size == 0:
            return False

        center_mean = float(center.mean())
        sat_mean = float(roi_hsv[:, :, 1].mean())
        # Filled egg body is bright enough — not a dark belt hole
        if center_mean >= 130.0:
            return False
        # Dark circular opening with low/medium saturation => hole
        if center_mean < 125.0 and sat_mean < 55.0 and long_side <= hole_diameter * 3.2:
            return True

        blur = cv2.GaussianBlur(roi_gray, (5, 5), 1)
        circles = cv2.HoughCircles(
            blur,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=max(8, short_side // 2),
            param1=50,
            param2=14,
            minRadius=max(4, int(short_side * 0.28)),
            maxRadius=max(6, int(short_side * 0.48)),
        )
        if circles is None:
            return False
        # Only treat as hole if the circle is dark inside
        return center_mean < 120.0

    def _passes_brown_egg_shape(
        self,
        frame: np.ndarray,
        bbox: tuple[int, int, int, int],
        hole_radius: float,
    ) -> bool:
        x1, y1, x2, y2 = bbox
        roi_gray = cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
        roi_hsv = cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2HSV)
        if not self._is_egg_sized_bbox(bbox, hole_radius):
            return False
        if not self._has_egg_color_signature(roi_gray, roi_hsv):
            return False

        margin_y = max(2, roi_gray.shape[0] // 5)
        margin_x = max(2, roi_gray.shape[1] // 5)
        center_gray = roi_gray[margin_y:-margin_y, margin_x:-margin_x]
        border_mask = np.ones(roi_gray.shape, dtype=np.uint8)
        border_mask[margin_y:-margin_y, margin_x:-margin_x] = 0
        border_gray = roi_gray[border_mask == 1]
        if center_gray.size == 0 or border_gray.size == 0:
            return False

        center_mean = float(center_gray.mean())
        border_mean = float(border_gray.mean())
        if center_mean < border_mean - 20.0 and center_mean < 130.0:
            return False

        aspect = (x2 - x1) / max(1.0, y2 - y1)
        if aspect < 0.45 or aspect > 2.1:
            return False

        return float(center_gray.std()) <= 52.0

    def _passes_low_contrast_egg_shape(
        self,
        frame: np.ndarray,
        bbox: tuple[int, int, int, int],
        hole_radius: float,
    ) -> bool:
        x1, y1, x2, y2 = bbox
        roi_gray = cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2HSV)
        height, width = roi_gray.shape
        if height < 12 or width < 12:
            return False

        if not self._is_egg_sized_bbox(bbox, hole_radius):
            return False

        sat_mean = float(hsv[:, :, 1].mean())
        gray_mean = float(roi_gray.mean())
        is_white_egg = sat_mean < 75 and gray_mean > 140
        if not is_white_egg:
            return False

        aspect = width / max(1.0, height)
        if aspect < 0.7 or aspect > 1.8:
            return False

        return float(roi_gray.std()) < 28.0

    def _is_hollow_belt_hole(
        self,
        frame: np.ndarray,
        bbox: tuple[int, int, int, int],
        hole_radius: float,
    ) -> bool:
        x1, y1, x2, y2 = bbox
        roi_gray = cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
        height, width = roi_gray.shape
        if height < 12 or width < 12:
            return False

        margin_y = max(2, height // 5)
        margin_x = max(2, width // 5)
        center_gray = roi_gray[margin_y:-margin_y, margin_x:-margin_x]
        border_mask = np.ones(roi_gray.shape, dtype=np.uint8)
        border_mask[margin_y:-margin_y, margin_x:-margin_x] = 0
        border_gray = roi_gray[border_mask == 1]
        if center_gray.size == 0 or border_gray.size == 0:
            return False

        center_mean = float(center_gray.mean())
        border_mean = float(border_gray.mean())
        if center_mean < border_mean - 12.0:
            return True

        max_hole_dim = max(48.0, hole_radius * 3.8)
        if min(height, width) > max_hole_dim:
            return False

        roi_std = float(roi_gray.std())
        if roi_std < 40.0:
            return False

        _, dark_mask = cv2.threshold(roi_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        dark_ratio = float((dark_mask > 0).mean())
        if dark_ratio < 0.10:
            return False

        contours, _ = cv2.findContours(dark_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return False

        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)
        if area < 0.10 * height * width:
            return False

        perimeter = cv2.arcLength(largest, True)
        if perimeter <= 0:
            return False

        circularity = 4.0 * np.pi * area / (perimeter * perimeter)
        return circularity >= 0.40

    def _is_on_irregular_belt(
        self,
        frame: np.ndarray,
        bbox: tuple[int, int, int, int],
        hole_radius: float,
    ) -> bool:
        if self._is_egg_sized_bbox(bbox, hole_radius):
            x1, y1, x2, y2 = bbox
            roi_gray = cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
            roi_hsv = cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2HSV)
            if self._has_egg_color_signature(roi_gray, roi_hsv):
                margin_y = max(2, roi_gray.shape[0] // 5)
                margin_x = max(2, roi_gray.shape[1] // 5)
                center_gray = roi_gray[margin_y:-margin_y, margin_x:-margin_x]
                border_mask = np.ones(roi_gray.shape, dtype=np.uint8)
                border_mask[margin_y:-margin_y, margin_x:-margin_x] = 0
                border_gray = roi_gray[border_mask == 1]
                if center_gray.size > 0 and border_gray.size > 0:
                    if float(roi_gray.std()) > 8.0 and float(center_gray.mean()) >= float(border_gray.mean()) - 12.0:
                        return False

        height, width = frame.shape[:2]
        center_x = (bbox[0] + bbox[2]) // 2
        center_y = (bbox[1] + bbox[3]) // 2
        window_radius = max(36, int(hole_radius * 4.5))

        x1 = max(0, center_x - window_radius)
        x2 = min(width, center_x + window_radius)
        y1 = max(0, center_y - window_radius)
        y2 = min(height, center_y + window_radius)
        patch = frame[y1:y2, x1:x2]
        if patch.size == 0:
            return True

        gray = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
        local_score = self._hole_regularity_score(gray, hole_radius)
        cache = self._frame_cache
        if cache is not None:
            frame_score = cache.frame_hole_score
        else:
            frame_score = self._hole_regularity_score(
                cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
                hole_radius,
            )
        threshold = max(0.08, frame_score * 0.5)
        return local_score <= threshold

    def _hole_regularity_score(self, strip_gray: np.ndarray, hole_radius: float) -> float:
        if strip_gray.size == 0:
            return 0.0

        blur = cv2.GaussianBlur(strip_gray, (9, 9), 2)
        circles = cv2.HoughCircles(
            blur,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=max(12.0, hole_radius * 1.4),
            param1=60,
            param2=18,
            minRadius=max(4, int(hole_radius * 0.65)),
            maxRadius=max(8, int(hole_radius * 1.35)),
        )
        if circles is None:
            return 0.0

        detected = circles[0]
        if len(detected) < 4:
            return len(detected) / 8.0

        radii = detected[:, 2]
        radius_mean = float(np.mean(radii))
        if radius_mean <= 0:
            return 0.0
        radius_cv = float(np.std(radii) / radius_mean)
        if radius_cv > 0.22:
            return 0.2

        centers = detected[:, :2]
        distances: list[float] = []
        for index, center in enumerate(centers):
            for other in centers[index + 1 :]:
                distances.append(float(np.linalg.norm(center - other)))
        if len(distances) < 3:
            return 0.3

        distance_mean = float(np.mean(distances))
        if distance_mean <= 0:
            return 0.0
        distance_cv = float(np.std(distances) / distance_mean)
        if distance_cv > 0.38:
            return 0.25

        count_score = min(1.0, len(detected) / 12.0)
        return count_score * (1.0 - radius_cv) * (1.0 - distance_cv * 0.5)

    def _is_filled_egg_blob(
        self,
        frame: np.ndarray,
        bbox: tuple[int, int, int, int],
        hole_radius: float,
    ) -> bool:
        x1, y1, x2, y2 = bbox
        roi_color = frame[y1:y2, x1:x2]
        if roi_color.size == 0:
            return False

        roi_gray = cv2.cvtColor(roi_color, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(roi_color, cv2.COLOR_BGR2HSV)
        height, width = roi_gray.shape
        if height < 12 or width < 12:
            return False

        margin_y = max(2, height // 5)
        margin_x = max(2, width // 5)
        center_gray = roi_gray[margin_y:-margin_y, margin_x:-margin_x]
        center_sat = hsv[margin_y:-margin_y, margin_x:-margin_x, 1]
        center_hue = hsv[margin_y:-margin_y, margin_x:-margin_x, 0]
        if center_gray.size == 0:
            return False

        border_mask = np.ones(roi_gray.shape, dtype=np.uint8)
        border_mask[margin_y:-margin_y, margin_x:-margin_x] = 0
        border_gray = roi_gray[border_mask == 1]
        border_sat = hsv[:, :, 1][border_mask == 1]
        if border_gray.size == 0 or border_sat.size == 0:
            return False

        center_mean = float(center_gray.mean())
        center_std = float(center_gray.std())
        border_mean = float(border_gray.mean())
        border_sat_mean = float(border_sat.mean())
        saturation_mean = float(center_sat.mean())
        hue_mean = float(center_hue.mean())

        if center_mean < border_mean - 20.0:
            return False

        is_white_egg = saturation_mean < 80 and center_mean > 125
        is_brown_egg = 5 <= hue_mean <= 62 and saturation_mean >= 18 and 95 < center_mean < 210
        if is_brown_egg and center_mean < border_mean - 8.0:
            return False
        max_center_std = 48.0 if is_brown_egg else 38.0
        if center_std > max_center_std:
            return False

        if not (is_white_egg or is_brown_egg):
            return False

        strong_egg_color = (is_brown_egg and saturation_mean > 80) or (
            is_white_egg and center_mean > 145
        )
        if not strong_egg_color and abs(center_mean - border_mean) < 8.0:
            return False

        if center_mean > border_mean + 15 and saturation_mean < border_sat_mean * 0.75:
            return False

        return self._is_egg_sized_bbox(bbox, hole_radius)


class Detector:
    def __init__(self, runtime: RuntimeConfig) -> None:
        self.runtime = runtime
        self.backend = self._build_backend(runtime)
        self._classic_fallback: ClassicBackend | None = None
        if runtime.backend in {"ultralytics", "roboflow", "ensemble"}:
            # Filtros de furo/esteira sobre deteccoes do modelo
            self._classic_fallback = ClassicBackend(
                RuntimeConfig(
                    backend="classic",
                    normalize=runtime.normalize,
                    reference_image=runtime.reference_image,
                    diff_threshold=runtime.diff_threshold,
                )
            )

    def detect(self, frame: np.ndarray, offset: tuple[int, int] = (0, 0)) -> list[Detection]:
        detections = self.backend.detect(frame)
        detections = [_normalize_egg_label(det) for det in detections]

        classic = self._classic_fallback
        if classic is not None:
            # Prefer YOLO trained on this belt; classic only fills high-quality misses
            hole_radius = classic._estimate_hole_radius(frame)
            yolo_keep = [
                det
                for det in detections
                if det.confidence >= max(0.28, self.runtime.confidence * 0.85)
                and self._is_clean_egg_box(frame, det.bbox, classic, hole_radius)
            ]
            yolo_keep = self._split_merged_egg_boxes(frame, yolo_keep, classic, hole_radius)
            # Do not merge classic: it reintroduces belt-hole / empty-belt FPs
            detections = self._nms_detections(yolo_keep, overlap_threshold=0.35)
        else:
            detections = self._filter_tiny(detections, frame)

        detections = self._filter_tiny(detections, frame)

        if offset == (0, 0):
            return detections

        translated: list[Detection] = []
        offset_x, offset_y = offset
        for detection in detections:
            x1, y1, x2, y2 = detection.bbox
            translated.append(
                Detection(
                    bbox=(x1 + offset_x, y1 + offset_y, x2 + offset_x, y2 + offset_y),
                    confidence=detection.confidence,
                    label=detection.label,
                )
            )
        return translated

    @staticmethod
    def _is_clean_egg_box(
        frame: np.ndarray,
        bbox: tuple[int, int, int, int],
        classic: ClassicBackend,
        hole_radius: float,
    ) -> bool:
        return (
            not classic._looks_like_belt_hole(frame, bbox, hole_radius)
            and not classic._is_perforated_belt_patch(frame, bbox)
            and classic._has_solid_egg_fill(frame, bbox)
            and classic._has_egg_body_color(frame, bbox)
        )

    @staticmethod
    def _filter_tiny(detections: list[Detection], frame: np.ndarray) -> list[Detection]:
        min_side = max(28, int(min(frame.shape[:2]) * 0.05))
        return [
            det
            for det in detections
            if (det.bbox[2] - det.bbox[0]) >= min_side and (det.bbox[3] - det.bbox[1]) >= min_side
        ]

    @staticmethod
    def _nms_detections(
        detections: list[Detection],
        overlap_threshold: float = 0.35,
    ) -> list[Detection]:
        """Keep highest-confidence box when two detections overlap heavily."""
        ordered = sorted(detections, key=lambda det: det.confidence, reverse=True)
        kept: list[Detection] = []
        for candidate in ordered:
            redundant = False
            for existing in kept:
                if _bbox_overlap_ratio(candidate.bbox, existing.bbox) >= overlap_threshold:
                    redundant = True
                    break
            if not redundant:
                kept.append(candidate)
        return kept

    def _split_merged_egg_boxes(
        self,
        frame: np.ndarray,
        detections: list[Detection],
        classic: ClassicBackend,
        hole_radius: float,
    ) -> list[Detection]:
        """Split oversized boxes that likely cover two touching eggs."""
        typical = classic._min_egg_dimension(hole_radius)
        split: list[Detection] = []
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            width = x2 - x1
            height = y2 - y1
            parts: list[tuple[int, int, int, int]] = []
            if width >= typical * 1.4 and width / max(1.0, height) >= 1.15:
                mid = (x1 + x2) // 2
                parts = [(x1, y1, mid, y2), (mid, y1, x2, y2)]
            elif height >= typical * 1.55 and height / max(1.0, width) >= 1.25:
                mid = (y1 + y2) // 2
                parts = [(x1, y1, x2, mid), (x1, mid, x2, y2)]
            else:
                split.append(det)
                continue

            kept = [
                Detection(bbox=part, confidence=det.confidence * 0.95, label=det.label)
                for part in parts
                if self._is_clean_egg_box(frame, part, classic, hole_radius)
            ]
            split.extend(kept if len(kept) >= 2 else [det])
        return split

    def _build_backend(self, runtime: RuntimeConfig) -> InferenceBackend:
        if runtime.backend == "classic":
            return ClassicBackend(runtime)

        if runtime.backend == "roboflow":
            return RoboflowBackend(runtime)

        if runtime.backend == "ensemble":
            return EnsembleBackend(runtime)

        if runtime.backend != "ultralytics":
            raise ValueError(f"Backend de inferencia nao suportado: {runtime.backend}")

        if runtime.target_label and Path(runtime.model_path).name == "yolov8n.pt":
            logger.warning(
                "`target_label` esta configurado, mas o peso atual e `yolov8n.pt`. "
                "Substitua por um modelo treinado para ovos para uso real."
            )

        return UltralyticsBackend(runtime)


def _normalize_egg_label(detection: Detection) -> Detection:
    label = detection.label.lower().strip()
    if label in {"ovo", "egg", "eggs"}:
        return Detection(bbox=detection.bbox, confidence=detection.confidence, label="egg")
    return detection


def _merge_detections(
    primary: list[Detection],
    secondary: list[Detection],
    overlap_threshold: float = 0.55,
) -> list[Detection]:
    """Merge YOLO + classic detections, avoiding duplicate boxes."""
    merged = list(primary)
    for candidate in secondary:
        overlaps = False
        for index, existing in enumerate(merged):
            if _bbox_overlap_ratio(candidate.bbox, existing.bbox) >= overlap_threshold:
                overlaps = True
                if candidate.confidence > existing.confidence:
                    merged[index] = candidate
                break
        if not overlaps:
            merged.append(candidate)
    return merged
