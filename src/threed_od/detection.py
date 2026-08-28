"""2D object detection backed by a pretrained YOLO model (Ultralytics)."""

from __future__ import annotations

from typing import Protocol

import numpy as np

from .schemas import BoundingBox, DetectedObject


def _class_name_for(names: dict[int, str] | list[str], class_id: int) -> str:
    if isinstance(names, dict):
        return names.get(class_id, str(class_id))
    if 0 <= class_id < len(names):
        return names[class_id]
    return str(class_id)


class Detector(Protocol):
    """Interface implemented by real and test-double detectors."""

    def predict(self, image_bgr: np.ndarray) -> list[DetectedObject]: ...

    @property
    def model_version(self) -> str: ...


class YoloDetector:
    """Wraps an Ultralytics YOLO model for 2D bounding-box detection.

    Uses pretrained COCO weights as-is -- no custom fine-tuning or accuracy
    claims are made beyond the upstream Ultralytics-published benchmarks
    (see docs/model-card.md).
    """

    def __init__(
        self, weights: str, device: str = "cpu", confidence_threshold: float = 0.35
    ) -> None:
        from ultralytics import YOLO  # imported lazily so tests can avoid torch/ultralytics cost

        self._model = YOLO(weights)
        self._device = device
        self._confidence_threshold = confidence_threshold
        self._weights_name = weights

    @property
    def model_version(self) -> str:
        return f"yolo:{self._weights_name}"

    def predict(self, image_bgr: np.ndarray) -> list[DetectedObject]:
        results = self._model.predict(
            image_bgr,
            device=self._device,
            conf=self._confidence_threshold,
            verbose=False,
        )
        detections: list[DetectedObject] = []
        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue
            names = result.names

            for box in boxes:
                xyxy = box.xyxy[0].tolist()
                class_id = int(box.cls[0].item())
                confidence = float(box.conf[0].item())
                detections.append(
                    DetectedObject(
                        class_name=_class_name_for(names, class_id),
                        confidence=confidence,
                        bbox=BoundingBox(
                            x_min=xyxy[0], y_min=xyxy[1], x_max=xyxy[2], y_max=xyxy[3]
                        ),
                    )
                )
        return detections
