"""Reproducible inference-latency benchmark, logged to local MLflow.

Measures end-to-end pipeline latency (detection + depth + calibration) on
CPU across a fixed set of synthetic frames at a documented resolution.
This measures OUR pipeline's latency; it does not re-measure the upstream
YOLOv8n / MiDaS_small accuracy benchmarks already published by their
authors (see docs/model-card.md for those citations).

Usage:
    python scripts/evaluate_latency.py --runs 20 --resolution 640x480
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import mlflow  # noqa: E402

from threed_od.config import get_settings  # noqa: E402
from threed_od.depth import MidasDepthEstimator  # noqa: E402
from threed_od.detection import YoloDetector  # noqa: E402
from threed_od.pipeline import DetectionPipeline, PipelineConfig  # noqa: E402

RESULTS_PATH = (
    Path(__file__).resolve().parent.parent / "docs" / "benchmarks" / "latency_results.json"
)


def parse_resolution(value: str) -> tuple[int, int]:
    width_str, height_str = value.lower().split("x")
    return int(width_str), int(height_str)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--resolution", type=str, default="640x480")
    parser.add_argument("--warmup", type=int, default=3)
    args = parser.parse_args()

    width, height = parse_resolution(args.resolution)
    settings = get_settings()

    mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
    mlflow.set_experiment(settings.mlflow_experiment_name)

    detector = YoloDetector(
        weights=settings.yolo_weights,
        device="cpu",
        confidence_threshold=settings.yolo_confidence_threshold,
    )
    depth_estimator = MidasDepthEstimator(model_name=settings.depth_model_name, device="cpu")
    config = PipelineConfig(
        focal_length_px=settings.camera_focal_length_px,
        principal_point_x=None,
        principal_point_y=None,
        default_object_height_m=settings.depth_reference_object_height_m,
    )
    pipeline = DetectionPipeline(detector, depth_estimator, config)

    rng = np.random.default_rng(seed=42)
    frame = rng.integers(0, 255, size=(height, width, 3), dtype=np.uint8)

    for _ in range(args.warmup):
        pipeline.run_on_image(frame, frame)

    latencies_ms: list[float] = []
    for _ in range(args.runs):
        start = time.perf_counter()
        pipeline.run_on_image(frame, frame)
        latencies_ms.append((time.perf_counter() - start) * 1000)

    latencies_ms.sort()
    p50 = statistics.median(latencies_ms)
    p95 = latencies_ms[int(0.95 * (len(latencies_ms) - 1))]
    mean = statistics.mean(latencies_ms)

    results = {
        "runs": args.runs,
        "resolution": f"{width}x{height}",
        "device": "cpu",
        "detector": detector.model_version,
        "depth_model": settings.depth_model_name,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "latency_ms_mean": round(mean, 2),
        "latency_ms_p50": round(p50, 2),
        "latency_ms_p95": round(p95, 2),
        "latency_ms_min": round(min(latencies_ms), 2),
        "latency_ms_max": round(max(latencies_ms), 2),
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")

    with mlflow.start_run(run_name="latency-benchmark"):
        mlflow.log_params({k: v for k, v in results.items() if not k.startswith("latency_ms")})
        mlflow.log_metrics({k: v for k, v in results.items() if k.startswith("latency_ms")})
        mlflow.log_artifact(str(RESULTS_PATH))

    print(json.dumps(results, indent=2))
    print(
        f"\nResults saved to {RESULTS_PATH} and logged to MLflow at {settings.mlflow_tracking_uri}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
