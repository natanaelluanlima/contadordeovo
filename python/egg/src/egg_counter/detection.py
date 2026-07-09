from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path

import cv2
import numpy as np

from egg_counter.config import RuntimeConfig
from egg_counter.models import Detection

logger = logging.getLogger(__name__)


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
                if self.runtime.target_label and label != self.runtime.target_label:
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


class ClassicBackend(InferenceBackend):
    """Detecta ovos ovais na esteira e ignora buracos circulares."""

    def __init__(self, runtime: RuntimeConfig) -> None:
        self.diff_threshold = runtime.diff_threshold
        self._reference_gray: np.ndarray | None = None

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
        hole_radius = self._estimate_hole_radius(frame)
        candidates: list[tuple[tuple[int, int, int, int], float, float]] = []

        reference_candidates: list[tuple[tuple[int, int, int, int], float, float]] = []
        reference_aligned = False
        if self._reference_gray is not None:
            reference_candidates = self._detect_by_reference_diff(frame, hole_radius)
            reference_aligned = self._is_reference_aligned(frame)

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

    def _is_reference_aligned(self, frame: np.ndarray) -> bool:
        if self._reference_gray is None:
            return False

        height, width = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        reference = cv2.resize(self._reference_gray, (width, height), interpolation=cv2.INTER_LINEAR)
        return float(cv2.absdiff(gray, reference).mean()) <= 30.0

    def _estimate_hole_radius(self, frame: np.ndarray) -> float:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
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

        height, width = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        reference = cv2.resize(self._reference_gray, (width, height), interpolation=cv2.INTER_LINEAR)
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
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        height, width = gray.shape[:2]
        saturation = hsv[:, :, 1]

        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
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
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
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
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
        )
        color_mask = cv2.morphologyEx(
            color_mask,
            cv2.MORPH_CLOSE,
            cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE,
                (max(9, int(hole_radius * 1.2)) | 1, max(11, int(hole_radius * 2.0)) | 1),
            ),
            iterations=1,
        )

        # Ovos marrons neste video aparecem nas colunas da esquerda da esteira.
        lane_mask = color_mask[:, : max(1, int(width * 0.55))].copy()
        lane_mask = cv2.erode(
            lane_mask,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)),
            iterations=2,
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
            if box_height > height * 0.4 or box_width > width * 0.25:
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
        dist = cv2.distanceTransform(roi_mask, cv2.DIST_L2, 5)
        candidates: list[tuple[tuple[int, int, int, int], float, float]] = []
        frame_height, frame_width = gray.shape[:2]

        if dist.max() > 0:
            _, sure_fg = cv2.threshold(dist, 0.42 * dist.max(), 255, 0)
            sure_fg = sure_fg.astype(np.uint8)
            sure_fg = cv2.erode(
                sure_fg,
                cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
                iterations=1,
            )
            sub_contours, _ = cv2.findContours(sure_fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in sub_contours:
                area = cv2.contourArea(contour)
                if area < min_area * 0.55:
                    continue

                sx, sy, sw, sh = cv2.boundingRect(contour)
                sub_bbox = (x_offset + x1 + sx, y1 + sy, x_offset + x1 + sx + sw, y1 + sy + sh)
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

        max_egg_height = self._min_egg_dimension(hole_radius) * 1.75
        candidates = [
            candidate
            for candidate in candidates
            if (candidate[0][3] - candidate[0][1]) <= max_egg_height
        ]

        if len(candidates) < 2 and (y2 - y1) > self._min_egg_dimension(hole_radius) * 2.0:
            mid_y = (y1 + y2) // 2
            for sub_bbox in ((x_offset + x1, y1, x_offset + x2, mid_y), (x_offset + x1, mid_y, x_offset + x2, y2)):
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

        return candidates

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

        roi_gray = gray[y1:y2, x1:x2]
        roi_hsv = hsv[y1:y2, x1:x2]
        if not self._has_egg_color_signature(roi_gray, roi_hsv):
            return None

        aspect = box_width / max(1.0, box_height)
        if aspect < 0.55 or aspect > 1.9:
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
        min_distance = max(45.0, hole_radius * 3.2)

        for bbox, confidence, score in sorted(candidates, key=lambda item: item[2], reverse=True):
            center_x = (bbox[0] + bbox[2]) / 2
            center_y = (bbox[1] + bbox[3]) / 2
            bbox_width = bbox[2] - bbox[0]
            bbox_height = bbox[3] - bbox[1]
            if any(
                (
                    (center_x - other_center_x) ** 2 + (center_y - other_center_y) ** 2
                    <= min_distance**2
                )
                or _bbox_overlap_ratio(bbox, other_bbox) >= 0.35
                for other_bbox, _, _, other_center_x, other_center_y in kept
            ):
                continue
            kept.append((bbox, confidence, score, center_x, center_y))

        return [(bbox, confidence) for bbox, confidence, _, _, _ in kept]

    def _remove_overlay_artifacts(self, frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
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
        if self._is_on_irregular_belt(frame, bbox, hole_radius):
            return False
        if self._passes_low_contrast_egg_shape(frame, bbox, hole_radius):
            return True
        if self._passes_brown_egg_shape(frame, bbox, hole_radius):
            return True
        return self._is_filled_egg_blob(frame, bbox, hole_radius)

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
        if aspect < 0.55 or aspect > 1.9:
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
        if center_mean < border_mean - 20.0:
            return True

        max_hole_dim = max(40.0, hole_radius * 3.4)
        if min(height, width) > max_hole_dim:
            return False

        roi_std = float(roi_gray.std())
        if roi_std < 52.0:
            return False

        _, dark_mask = cv2.threshold(roi_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        dark_ratio = float((dark_mask > 0).mean())
        if dark_ratio < 0.12:
            return False

        contours, _ = cv2.findContours(dark_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return False

        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)
        if area < 0.12 * height * width:
            return False

        perimeter = cv2.arcLength(largest, True)
        if perimeter <= 0:
            return False

        circularity = 4.0 * np.pi * area / (perimeter * perimeter)
        return circularity >= 0.45

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
        frame_score = self._hole_regularity_score(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), hole_radius)
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

    def detect(self, frame: np.ndarray, offset: tuple[int, int] = (0, 0)) -> list[Detection]:
        detections = self.backend.detect(frame)
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

    def _build_backend(self, runtime: RuntimeConfig) -> InferenceBackend:
        if runtime.backend == "classic":
            return ClassicBackend(runtime)

        if runtime.backend != "ultralytics":
            raise ValueError(f"Backend de inferencia nao suportado: {runtime.backend}")

        if runtime.target_label and Path(runtime.model_path).name == "yolov8n.pt":
            logger.warning(
                "`target_label` esta configurado, mas o peso atual e `yolov8n.pt`. "
                "Substitua por um modelo treinado para ovos para uso real."
            )

        return UltralyticsBackend(runtime)
