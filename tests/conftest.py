"""Shared pytest fixtures.

Contract and unit tests use fake Detector/DepthEstimator test doubles so
the fast test suite never needs to download YOLO/MiDaS weights or import
torch. The one real-model integration test lives in
tests/integration/test_real_pipeline.py and is marked `model_download`.
"""

from __future__ import annotations

import io

import numpy as np
import pytest
from PIL import Image

from threed_od.schemas import BoundingBox, DetectedObject


class FakeDetector:
    model_version = "fake-detector:v1"

    def __init__(self, detections: list[DetectedObject] | None = None) -> None:
        self._detections = detections if detections is not None else self._default_detections()

    @staticmethod
    def _default_detections() -> list[DetectedObject]:
        return [
            DetectedObject(
                class_name="person",
                confidence=0.91,
                bbox=BoundingBox(x_min=10, y_min=10, x_max=60, y_max=150),
            )
        ]

    def predict(self, image_bgr: np.ndarray) -> list[DetectedObject]:
        return [d.model_copy(deep=True) for d in self._detections]


class FakeDepthEstimator:
    def relative_depth_map(self, image_rgb: np.ndarray) -> np.ndarray:
        return np.ones(image_rgb.shape[:2], dtype=np.float32)

    def relative_depth_at_bbox(self, depth_map: np.ndarray, bbox: BoundingBox) -> float:
        return 1.0


@pytest.fixture
def fake_detector() -> FakeDetector:
    return FakeDetector()


@pytest.fixture
def fake_depth_estimator() -> FakeDepthEstimator:
    return FakeDepthEstimator()


def make_test_image_bytes(width: int = 200, height: int = 200, fmt: str = "PNG") -> bytes:
    """Generate a small synthetic in-memory image, avoiding any bundled third-party media."""
    array = np.zeros((height, width, 3), dtype=np.uint8)
    array[:, :] = (60, 120, 180)
    array[20:140, 20:70] = (200, 200, 200)  # a lighter rectangle "object" region
    image = Image.fromarray(array)
    buffer = io.BytesIO()
    image.save(buffer, format=fmt)
    return buffer.getvalue()


@pytest.fixture
def sample_image_bytes() -> bytes:
    return make_test_image_bytes()
