"""FastAPI application exposing image and video 3D-aware object detection."""

from __future__ import annotations

import logging
import os
import tempfile
import time

import cv2
import numpy as np
import structlog
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from ..config import Settings, get_settings
from ..jobs import JobStore
from ..pipeline import DetectionPipeline
from ..schemas import (
    FrameResult,
    HealthResponse,
    ImageInferenceResponse,
    JobStatusResponse,
    JobSubmissionResponse,
    ReadinessResponse,
    VideoInferenceResult,
)
from ..telemetry import DETECTED_OBJECTS_TOTAL, INFERENCE_LATENCY_SECONDS, INFERENCE_REQUESTS_TOTAL
from . import deps

logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger("threed_od.api")

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/avi", "video/quicktime", "video/x-matroska"}

app = FastAPI(
    title="3D Object Detection System API",
    version="0.1.0",
    description="YOLO detection + monocular depth + calibration for approximate 3D position.",
)


def _configure_cors(fastapi_app: FastAPI, settings: Settings) -> None:
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list(),
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )


_configure_cors(app, get_settings())


async def _read_upload_within_limit(file: UploadFile, max_size_mb: int) -> bytes:
    max_bytes = max_size_mb * 1024 * 1024
    data = await file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {max_size_mb}MB upload limit",
        )
    if len(data) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Uploaded file is empty"
        )
    return data


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        detector_loaded=deps.get_detector.cache_info().currsize > 0,
        depth_model_loaded=deps.get_depth_estimator.cache_info().currsize > 0,
    )


@app.get("/ready", response_model=ReadinessResponse)
def ready(settings: Settings = Depends(get_settings)) -> ReadinessResponse:
    checks: dict[str, bool] = {}
    try:
        deps.get_storage()
        checks["storage"] = True
    except Exception:  # noqa: BLE001 - readiness check must not raise
        checks["storage"] = False
    return ReadinessResponse(ready=all(checks.values()), checks=checks)


@app.get("/metrics")
def metrics() -> Response:
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/v1/infer/image", response_model=ImageInferenceResponse)
async def infer_image(
    file: UploadFile,
    settings: Settings = Depends(get_settings),
    pipeline: DetectionPipeline = Depends(deps.get_pipeline),
) -> ImageInferenceResponse:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        INFERENCE_REQUESTS_TOTAL.labels(endpoint="infer_image", outcome="rejected").inc()
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported content type {file.content_type!r}; "
                f"expected one of {sorted(ALLOWED_IMAGE_TYPES)}"
            ),
        )

    raw = await _read_upload_within_limit(file, settings.max_upload_size_mb)
    array = np.frombuffer(raw, dtype=np.uint8)
    image_bgr = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image_bgr is None:
        INFERENCE_REQUESTS_TOTAL.labels(endpoint="infer_image", outcome="invalid").inc()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Could not decode image"
        )

    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    with INFERENCE_LATENCY_SECONDS.labels(endpoint="infer_image").time():
        result = pipeline.run_on_image(image_bgr, image_rgb)

    for obj in result.objects:
        DETECTED_OBJECTS_TOTAL.labels(class_name=obj.class_name).inc()
    INFERENCE_REQUESTS_TOTAL.labels(endpoint="infer_image", outcome="success").inc()
    return result


def _process_video_job(
    job_id: str,
    video_path: str,
    pipeline: DetectionPipeline,
    job_store: JobStore,
    max_duration_s: int,
) -> None:
    job_store.mark_processing(job_id)
    try:
        capture = cv2.VideoCapture(video_path)
        fps = capture.get(cv2.CAP_PROP_FPS) or 0.0
        frame_count_total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if fps > 0 and frame_count_total / fps > max_duration_s:
            raise ValueError(f"Video exceeds the {max_duration_s}s duration limit")

        tracker = deps.new_tracker()
        frames: list[FrameResult] = []
        frame_index = 0
        start = time.perf_counter()

        while True:
            success, frame_bgr = capture.read()
            if not success:
                break
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            objects = pipeline.run_on_frame(frame_bgr, frame_rgb, tracker)
            timestamp_s = frame_index / fps if fps > 0 else float(frame_index)
            frames.append(
                FrameResult(frame_index=frame_index, timestamp_s=timestamp_s, objects=objects)
            )
            frame_index += 1
        capture.release()

        total_latency_ms = (time.perf_counter() - start) * 1000
        result = VideoInferenceResult(
            frames=frames,
            frame_count=frame_index,
            fps=fps,
            total_latency_ms=round(total_latency_ms, 2),
            model_version=pipeline._detector.model_version,  # noqa: SLF001
        )
        job_store.mark_completed(job_id, result)
        INFERENCE_REQUESTS_TOTAL.labels(endpoint="infer_video", outcome="success").inc()
    except Exception as exc:  # noqa: BLE001 - surfaced via job status, not a crash
        logger.error("video_job_failed", job_id=job_id, error=str(exc))
        job_store.mark_failed(job_id, str(exc))
        INFERENCE_REQUESTS_TOTAL.labels(endpoint="infer_video", outcome="failed").inc()
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)


@app.post(
    "/v1/infer/video", response_model=JobSubmissionResponse, status_code=status.HTTP_202_ACCEPTED
)
async def infer_video(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(get_settings),
    pipeline: DetectionPipeline = Depends(deps.get_pipeline),
    job_store: JobStore = Depends(deps.get_job_store),
) -> JobSubmissionResponse:
    if file.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported content type {file.content_type!r}; "
                f"expected one of {sorted(ALLOWED_VIDEO_TYPES)}"
            ),
        )

    raw = await _read_upload_within_limit(file, settings.max_upload_size_mb)
    suffix = os.path.splitext(file.filename or "upload.mp4")[1] or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(raw)
        video_path = tmp.name

    job = job_store.create()
    background_tasks.add_task(
        _process_video_job,
        job.job_id,
        video_path,
        pipeline,
        job_store,
        settings.max_video_duration_s,
    )
    return JobSubmissionResponse(job_id=job.job_id, status=job.status)


@app.get("/v1/jobs/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str, job_store: JobStore = Depends(deps.get_job_store)) -> JobStatusResponse:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id!r} not found"
        )
    return JobStatusResponse(
        job_id=job.job_id, status=job.status, error=job.error, result=job.result
    )
