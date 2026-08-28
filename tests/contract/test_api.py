from __future__ import annotations

import time

import cv2
import numpy as np
from fastapi.testclient import TestClient

from tests.conftest import make_test_image_bytes


def test_health_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_ok(client: TestClient) -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["ready"] is True


def test_metrics_exposes_prometheus_format(client: TestClient) -> None:
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "threed_od" in response.text or response.text == ""


def test_infer_image_success_contains_required_fields(client: TestClient) -> None:
    files = {"file": ("test.png", make_test_image_bytes(), "image/png")}
    response = client.post("/v1/infer/image", files=files)

    assert response.status_code == 200
    body = response.json()
    assert body["image_width"] == 200
    assert body["image_height"] == 200
    assert body["inference_latency_ms"] >= 0
    assert len(body["objects"]) == 1

    obj = body["objects"][0]
    assert obj["class_name"] == "person"
    assert 0.0 <= obj["confidence"] <= 1.0
    assert set(obj["bbox"].keys()) == {"x_min", "y_min", "x_max", "y_max"}
    assert obj["depth_m"] is not None
    assert obj["position_3d"] is not None
    assert set(obj["position_3d"].keys()) == {"x_m", "y_m", "z_m"}


def test_infer_image_rejects_unsupported_content_type(client: TestClient) -> None:
    files = {"file": ("test.txt", b"not an image", "text/plain")}
    response = client.post("/v1/infer/image", files=files)
    assert response.status_code == 415


def test_infer_image_rejects_empty_file(client: TestClient) -> None:
    files = {"file": ("test.png", b"", "image/png")}
    response = client.post("/v1/infer/image", files=files)
    assert response.status_code == 422


def test_infer_image_rejects_corrupt_image_bytes(client: TestClient) -> None:
    files = {"file": ("test.png", b"\x89PNG not a real png body", "image/png")}
    response = client.post("/v1/infer/image", files=files)
    assert response.status_code == 422


def test_get_job_not_found_returns_404(client: TestClient) -> None:
    response = client.get("/v1/jobs/does-not-exist")
    assert response.status_code == 404


def _make_tiny_video_bytes(tmp_path, frame_count: int = 5) -> bytes:
    path = tmp_path / "sample.mp4"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 5.0, (64, 64))
    for _ in range(frame_count):
        frame = np.zeros((64, 64, 3), dtype=np.uint8)
        writer.write(frame)
    writer.release()
    return path.read_bytes()


def test_infer_video_end_to_end_completes_with_frame_results(client: TestClient, tmp_path) -> None:
    video_bytes = _make_tiny_video_bytes(tmp_path)
    files = {"file": ("clip.mp4", video_bytes, "video/mp4")}

    submit_response = client.post("/v1/infer/video", files=files)
    assert submit_response.status_code == 202
    job_id = submit_response.json()["job_id"]

    deadline = time.time() + 10
    status_body = None
    while time.time() < deadline:
        status_response = client.get(f"/v1/jobs/{job_id}")
        assert status_response.status_code == 200
        status_body = status_response.json()
        if status_body["status"] in ("completed", "failed"):
            break
        time.sleep(0.1)

    assert status_body is not None
    assert status_body["status"] == "completed", status_body
    result = status_body["result"]
    assert result["frame_count"] >= 1
    assert len(result["frames"]) == result["frame_count"]
    first_frame_objects = result["frames"][0]["objects"]
    assert first_frame_objects[0]["track_id"] is not None


def test_infer_video_rejects_unsupported_content_type(client: TestClient) -> None:
    files = {"file": ("clip.txt", b"not a video", "text/plain")}
    response = client.post("/v1/infer/video", files=files)
    assert response.status_code == 415
