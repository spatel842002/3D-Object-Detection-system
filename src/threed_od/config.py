"""Environment-driven configuration with fail-fast validation.

All settings have safe local defaults so the service starts with zero
configuration for local development. Production deployments override
these via environment variables (see .env.example and
docs/environment-variables.md).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Model configuration ---
    yolo_weights: str = Field(default="yolov8n.pt", alias="YOLO_WEIGHTS")
    yolo_confidence_threshold: float = Field(default=0.35, alias="YOLO_CONFIDENCE_THRESHOLD")
    yolo_device: str = Field(default="cpu", alias="YOLO_DEVICE")

    depth_model_name: str = Field(default="MiDaS_small", alias="DEPTH_MODEL_NAME")
    depth_device: str = Field(default="cpu", alias="DEPTH_DEVICE")

    # --- Camera calibration (defaults are documented approximations, not a
    # calibrated device — see docs/calibration-guide.md) ---
    camera_focal_length_px: float = Field(default=721.5, alias="CAMERA_FOCAL_LENGTH_PX")
    camera_principal_point_x: float | None = Field(default=None, alias="CAMERA_PRINCIPAL_POINT_X")
    camera_principal_point_y: float | None = Field(default=None, alias="CAMERA_PRINCIPAL_POINT_Y")
    depth_reference_object_height_m: float = Field(
        default=1.7, alias="DEPTH_REFERENCE_OBJECT_HEIGHT_M"
    )

    # --- Object storage (MinIO locally, S3-compatible in production) ---
    s3_endpoint_url: str = Field(default="http://localhost:9000", alias="S3_ENDPOINT_URL")
    s3_access_key: str = Field(default="minioadmin", alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field(default="minioadmin", alias="S3_SECRET_KEY")
    s3_bucket_name: str = Field(default="threed-od-artifacts", alias="S3_BUCKET_NAME")
    s3_region: str = Field(default="us-east-1", alias="S3_REGION")
    s3_use_ssl: bool = Field(default=False, alias="S3_USE_SSL")
    storage_backend: str = Field(default="local", alias="STORAGE_BACKEND")
    local_storage_dir: str = Field(default="./data/artifacts", alias="LOCAL_STORAGE_DIR")

    # --- MLflow experiment tracking ---
    mlflow_tracking_uri: str = Field(default="file:./mlruns", alias="MLFLOW_TRACKING_URI")
    mlflow_experiment_name: str = Field(
        default="3d-object-detection", alias="MLFLOW_EXPERIMENT_NAME"
    )

    # --- Observability ---
    otel_exporter_otlp_endpoint: str | None = Field(
        default=None, alias="OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    otel_service_name: str = Field(default="threed-od-api", alias="OTEL_SERVICE_NAME")
    enable_metrics: bool = Field(default=True, alias="ENABLE_METRICS")

    # --- API ---
    max_upload_size_mb: int = Field(default=25, alias="MAX_UPLOAD_SIZE_MB")
    max_video_duration_s: int = Field(default=30, alias="MAX_VIDEO_DURATION_S")
    job_result_ttl_s: int = Field(default=3600, alias="JOB_RESULT_TTL_S")
    api_cors_origins: str = Field(default="http://localhost:5173", alias="API_CORS_ORIGINS")

    @field_validator("storage_backend")
    @classmethod
    def _validate_backend(cls, value: str) -> str:
        allowed = {"local", "s3"}
        if value not in allowed:
            raise ValueError(f"STORAGE_BACKEND must be one of {allowed}, got {value!r}")
        return value

    @field_validator("yolo_confidence_threshold")
    @classmethod
    def _validate_confidence(cls, value: float) -> float:
        if not 0.0 < value <= 1.0:
            raise ValueError("YOLO_CONFIDENCE_THRESHOLD must be in (0, 1]")
        return value

    @field_validator("max_upload_size_mb", "max_video_duration_s", "job_result_ttl_s")
    @classmethod
    def _validate_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("value must be a positive integer")
        return value

    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]

    def ensure_local_storage_dir(self) -> Path:
        path = Path(self.local_storage_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    """Return a process-wide cached, validated Settings instance.

    Raises pydantic.ValidationError with actionable field-level messages if
    the environment is misconfigured, so the process fails fast on startup
    rather than at first request.
    """
    return Settings()
