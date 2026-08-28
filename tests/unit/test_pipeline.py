from __future__ import annotations

import numpy as np

from tests.conftest import FakeDepthEstimator, FakeDetector
from threed_od.pipeline import DetectionPipeline, PipelineConfig
from threed_od.tracking import IouTracker


def _pipeline() -> DetectionPipeline:
    config = PipelineConfig(
        focal_length_px=700.0,
        principal_point_x=None,
        principal_point_y=None,
        default_object_height_m=1.7,
    )
    return DetectionPipeline(FakeDetector(), FakeDepthEstimator(), config)


def test_run_on_image_populates_depth_and_3d_position() -> None:
    pipeline = _pipeline()
    image = np.zeros((200, 200, 3), dtype=np.uint8)

    response = pipeline.run_on_image(image, image)

    assert response.image_width == 200
    assert response.image_height == 200
    assert len(response.objects) == 1
    obj = response.objects[0]
    assert obj.depth_m is not None and obj.depth_m > 0
    assert obj.position_3d is not None
    assert response.inference_latency_ms >= 0
    assert response.model_version == "fake-detector:v1"


def test_run_on_frame_assigns_track_ids_across_calls() -> None:
    pipeline = _pipeline()
    tracker = IouTracker()
    image = np.zeros((200, 200, 3), dtype=np.uint8)

    first = pipeline.run_on_frame(image, image, tracker)
    second = pipeline.run_on_frame(image, image, tracker)

    assert first[0].track_id == second[0].track_id
