"""End-to-end test against the REAL pretrained YOLOv8n + MiDaS_small weights.

Marked `model_download` because it downloads ~10-50MB of pretrained weights
on first run and requires network access. Skipped automatically in
environments without network egress. Run explicitly with:

    pytest -m model_download -v
"""

from __future__ import annotations

import socket

import numpy as np
import pytest

from threed_od.depth import MidasDepthEstimator
from threed_od.detection import YoloDetector
from threed_od.pipeline import DetectionPipeline, PipelineConfig


def _network_available() -> bool:
    try:
        socket.create_connection(("github.com", 443), timeout=3).close()
        return True
    except OSError:
        return False


pytestmark = pytest.mark.model_download


@pytest.fixture(scope="module")
def real_pipeline() -> DetectionPipeline:
    if not _network_available():
        pytest.skip("network unavailable; cannot download real model weights")
    detector = YoloDetector(weights="yolov8n.pt", device="cpu", confidence_threshold=0.25)
    depth_estimator = MidasDepthEstimator(model_name="MiDaS_small", device="cpu")
    config = PipelineConfig(
        focal_length_px=721.5,
        principal_point_x=None,
        principal_point_y=None,
        default_object_height_m=1.7,
    )
    return DetectionPipeline(detector, depth_estimator, config)


def test_real_pipeline_runs_end_to_end_on_synthetic_frame(real_pipeline: DetectionPipeline) -> None:
    # A synthetic frame is used here only to prove the real model wiring
    # executes without error and returns a schema-valid response; it is not
    # expected to contain recognizable COCO objects. See
    # scripts/run_real_demo.py for detection quality evidence on a real,
    # properly licensed photo.
    image = np.random.default_rng(seed=0).integers(0, 255, size=(480, 640, 3), dtype=np.uint8)
    response = real_pipeline.run_on_image(image, image)

    assert response.model_version == "yolo:yolov8n.pt"
    assert response.image_width == 640
    assert response.image_height == 480
    assert response.inference_latency_ms > 0
    for obj in response.objects:
        assert obj.confidence >= 0.25
        assert obj.depth_m is None or obj.depth_m > 0
