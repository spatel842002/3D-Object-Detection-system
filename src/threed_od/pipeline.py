"""End-to-end inference pipeline: detect -> estimate depth -> localize -> track."""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from .calibration import CameraIntrinsics, estimate_metric_depth_m, pixel_to_3d
from .depth import DepthEstimator
from .detection import Detector
from .schemas import DetectedObject, ImageInferenceResponse
from .tracking import IouTracker


@dataclass
class PipelineConfig:
    focal_length_px: float
    principal_point_x: float | None
    principal_point_y: float | None
    default_object_height_m: float


class DetectionPipeline:
    """Wires together a Detector and a DepthEstimator into full 3D-aware results."""

    def __init__(
        self, detector: Detector, depth_estimator: DepthEstimator, config: PipelineConfig
    ) -> None:
        self._detector = detector
        self._depth_estimator = depth_estimator
        self._config = config

    def _localize(
        self, detections: list[DetectedObject], depth_map: np.ndarray, image_shape: tuple[int, int]
    ) -> None:
        height, width = image_shape
        intrinsics = CameraIntrinsics.from_image_size(
            image_width=width,
            image_height=height,
            focal_length_px=self._config.focal_length_px,
            principal_point_x=self._config.principal_point_x,
            principal_point_y=self._config.principal_point_y,
        )
        for detection in detections:
            depth_m = estimate_metric_depth_m(
                class_name=detection.class_name,
                bbox=detection.bbox,
                focal_length_px=self._config.focal_length_px,
                default_height_m=self._config.default_object_height_m,
            )
            if depth_m is None:
                continue
            detection.depth_m = round(depth_m, 3)
            detection.position_3d = pixel_to_3d(detection.bbox, depth_m, intrinsics)

    def run_on_image(self, image_bgr: np.ndarray, image_rgb: np.ndarray) -> ImageInferenceResponse:
        start = time.perf_counter()
        detections = self._detector.predict(image_bgr)
        depth_map = self._depth_estimator.relative_depth_map(image_rgb)
        height, width = image_bgr.shape[:2]
        self._localize(detections, depth_map, (height, width))
        latency_ms = (time.perf_counter() - start) * 1000

        return ImageInferenceResponse(
            objects=detections,
            image_width=width,
            image_height=height,
            inference_latency_ms=round(latency_ms, 2),
            model_version=self._detector.model_version,
        )

    def run_on_frame(
        self, image_bgr: np.ndarray, image_rgb: np.ndarray, tracker: IouTracker
    ) -> list[DetectedObject]:
        detections = self._detector.predict(image_bgr)
        depth_map = self._depth_estimator.relative_depth_map(image_rgb)
        height, width = image_bgr.shape[:2]
        self._localize(detections, depth_map, (height, width))
        return tracker.update(detections)
