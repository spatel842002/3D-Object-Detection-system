from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.conftest import FakeDepthEstimator, FakeDetector
from threed_od.api import deps
from threed_od.api.app import app
from threed_od.pipeline import DetectionPipeline, PipelineConfig


@pytest.fixture
def client() -> TestClient:
    config = PipelineConfig(
        focal_length_px=700.0,
        principal_point_x=None,
        principal_point_y=None,
        default_object_height_m=1.7,
    )
    fake_pipeline = DetectionPipeline(FakeDetector(), FakeDepthEstimator(), config)

    app.dependency_overrides[deps.get_pipeline] = lambda: fake_pipeline
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
