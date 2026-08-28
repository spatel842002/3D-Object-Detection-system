"""Lazily-constructed, process-wide singletons for models, storage, and job state.

Kept separate from app.py so tests can override each provider via FastAPI's
dependency_overrides without importing torch/ultralytics at all.
"""

from __future__ import annotations

from functools import lru_cache

from ..config import get_settings
from ..depth import DepthEstimator, MidasDepthEstimator
from ..detection import Detector, YoloDetector
from ..jobs import JobStore
from ..pipeline import DetectionPipeline, PipelineConfig
from ..storage import ObjectStorage, build_storage_from_settings
from ..tracking import IouTracker


@lru_cache
def get_detector() -> Detector:
    settings = get_settings()
    return YoloDetector(
        weights=settings.yolo_weights,
        device=settings.yolo_device,
        confidence_threshold=settings.yolo_confidence_threshold,
    )


@lru_cache
def get_depth_estimator() -> DepthEstimator:
    settings = get_settings()
    return MidasDepthEstimator(model_name=settings.depth_model_name, device=settings.depth_device)


@lru_cache
def get_pipeline() -> DetectionPipeline:
    settings = get_settings()
    config = PipelineConfig(
        focal_length_px=settings.camera_focal_length_px,
        principal_point_x=settings.camera_principal_point_x,
        principal_point_y=settings.camera_principal_point_y,
        default_object_height_m=settings.depth_reference_object_height_m,
    )
    return DetectionPipeline(get_detector(), get_depth_estimator(), config)


@lru_cache
def get_storage() -> ObjectStorage:
    return build_storage_from_settings(get_settings())


@lru_cache
def get_job_store() -> JobStore:
    return JobStore(ttl_s=get_settings().job_result_ttl_s)


def new_tracker() -> IouTracker:
    return IouTracker()
