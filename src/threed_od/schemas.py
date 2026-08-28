"""Typed API contracts shared by the pipeline and the FastAPI layer."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x_min: float
    y_min: float
    x_max: float
    y_max: float


class Point3D(BaseModel):
    x_m: float = Field(description="Approximate lateral position in meters, camera-relative")
    y_m: float = Field(description="Approximate vertical position in meters, camera-relative")
    z_m: float = Field(description="Approximate forward depth in meters, camera-relative")


class DetectedObject(BaseModel):
    class_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: BoundingBox
    track_id: int | None = Field(
        default=None, description="Stable identifier across frames; null for single-image inference"
    )
    depth_m: float | None = Field(
        default=None,
        description="Estimated approximate depth to the object center, in meters. See "
        "docs/calibration-guide.md for the scale-recovery assumptions and error bounds.",
    )
    position_3d: Point3D | None = Field(
        default=None,
        description="Approximate camera-relative 3D position, or null if depth is unavailable",
    )


class ImageInferenceResponse(BaseModel):
    objects: list[DetectedObject]
    image_width: int
    image_height: int
    inference_latency_ms: float
    model_version: str


class JobStatusEnum(StrEnum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class FrameResult(BaseModel):
    frame_index: int
    timestamp_s: float
    objects: list[DetectedObject]


class VideoInferenceResult(BaseModel):
    frames: list[FrameResult]
    frame_count: int
    fps: float
    total_latency_ms: float
    model_version: str


class JobSubmissionResponse(BaseModel):
    job_id: str
    status: JobStatusEnum


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatusEnum
    error: str | None = None
    result: VideoInferenceResult | None = None


class HealthResponse(BaseModel):
    status: str
    detector_loaded: bool
    depth_model_loaded: bool


class ReadinessResponse(BaseModel):
    ready: bool
    checks: dict[str, bool]
