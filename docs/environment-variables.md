# Environment Variables

All variables are validated at startup by `src/threed_od/config.py`
(`pydantic-settings`); an invalid value fails fast with a field-level
error message rather than failing later at request time. Every variable
has a safe local default, so none are required for local development.
Copy `.env.example` to `.env` to override.

## Models

| Variable | Default | Notes |
|---|---|---|
| `YOLO_WEIGHTS` | `yolov8n.pt` | Ultralytics weights name or path; auto-downloaded if a bare name. |
| `YOLO_CONFIDENCE_THRESHOLD` | `0.35` | Must be in `(0, 1]`. |
| `YOLO_DEVICE` | `cpu` | Set to `cuda` for GPU deployment (see `docs/deployment.md`). |
| `DEPTH_MODEL_NAME` | `MiDaS_small` | Passed to `torch.hub.load("intel-isl/MiDaS", ...)`. |
| `DEPTH_DEVICE` | `cpu` | Set to `cuda` for GPU deployment. |

## Camera calibration

| Variable | Default | Notes |
|---|---|---|
| `CAMERA_FOCAL_LENGTH_PX` | `721.5` | KITTI-derived default; calibrate your own camera for accurate results (see `docs/calibration-guide.md`). |
| `CAMERA_PRINCIPAL_POINT_X` / `_Y` | unset (defaults to image center) | Override if you have calibrated principal-point offsets. |
| `DEPTH_REFERENCE_OBJECT_HEIGHT_M` | `1.7` | Fallback real-world height (meters) for object classes not in the typical-height table. |

## Object storage

| Variable | Default | Notes |
|---|---|---|
| `STORAGE_BACKEND` | `local` | `local` or `s3`. |
| `LOCAL_STORAGE_DIR` | `./data/artifacts` | Used when `STORAGE_BACKEND=local`. |
| `S3_ENDPOINT_URL` | `http://localhost:9000` | MinIO locally; omit/point at AWS for production. |
| `S3_ACCESS_KEY` / `S3_SECRET_KEY` | `minioadmin` / `minioadmin` | **Change for any non-local deployment.** In production, source from a secrets manager, never a committed `.env`. |
| `S3_BUCKET_NAME` | `threed-od-artifacts` | Auto-created if missing (`head_bucket` / `create_bucket`). |
| `S3_REGION` | `us-east-1` | |
| `S3_USE_SSL` | `false` | Set `true` for AWS S3 / any TLS endpoint. |

## MLflow

| Variable | Default | Notes |
|---|---|---|
| `MLFLOW_TRACKING_URI` | `file:./mlruns` | Point at a remote MLflow server URI for shared tracking. |
| `MLFLOW_EXPERIMENT_NAME` | `3d-object-detection` | |

## Observability

| Variable | Default | Notes |
|---|---|---|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | unset (tracing disabled) | Point at an OpenTelemetry Collector, or a hosted OTLP ingest endpoint (Datadog, Azure Monitor, etc.). |
| `OTEL_SERVICE_NAME` | `threed-od-api` | |
| `ENABLE_METRICS` | `true` | Reserved for future use to disable `/metrics`; Prometheus client always registers metrics today. |

## API limits

| Variable | Default | Notes |
|---|---|---|
| `MAX_UPLOAD_SIZE_MB` | `25` | Enforced before decoding, via a bounded read. |
| `MAX_VIDEO_DURATION_S` | `30` | Enforced after opening the video (duration isn't known until then). |
| `JOB_RESULT_TTL_S` | `3600` | In-memory job records older than this are evicted. |
| `API_CORS_ORIGINS` | `http://localhost:5173` | Comma-separated list. |

## Production-only variables (no account required to define, but inert until one exists)

None of the variables above require a paid account to run this service
locally. For hosted production deployment, see
`docs/account-activation-checklist.md` for the exact accounts, resources,
and values these same variables should be set to (a managed S3 bucket
instead of MinIO, a hosted OTLP collector endpoint, etc.).
