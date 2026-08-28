# API Reference

Interactive OpenAPI docs are served at `/docs` (Swagger UI) and `/redoc`
when the app is running; the raw schema is at `/openapi.json`. This page
is the human-readable contract summary.

## `GET /health`

Liveness check. Never touches models or external services.

```json
{"status": "ok", "detector_loaded": true, "depth_model_loaded": true}
```

## `GET /ready`

Readiness check: verifies the configured `ObjectStorage` backend is
constructible. Returns `200` always; check the `ready` field.

```json
{"ready": true, "checks": {"storage": true}}
```

## `GET /metrics`

Prometheus exposition format. See `docs/observability.md`.

## `POST /v1/infer/image`

Synchronous single-image inference.

- **Request:** `multipart/form-data`, field `file`, content-type one of
  `image/jpeg`, `image/png`, `image/webp`. Max size `MAX_UPLOAD_SIZE_MB`
  (default 25MB).
- **Response `200`:**

```json
{
  "objects": [
    {
      "class_name": "person",
      "confidence": 0.7413988709449768,
      "bbox": {"x_min": 2353.62, "y_min": 1283.14, "x_max": 2527.09, "y_max": 1662.22},
      "track_id": null,
      "depth_m": 3.236,
      "position_3d": {"x_m": 5.204, "y_m": 2.299, "z_m": 3.236}
    }
  ],
  "image_width": 2560,
  "image_height": 1920,
  "inference_latency_ms": 754.77,
  "model_version": "yolo:yolov8n.pt"
}
```

(This example is drawn from the real recorded output in
`docs/assets/screenshots/image_inference_demo_result.json`.)

- **Errors:**
  - `415` -- unsupported content type
  - `413` -- file exceeds `MAX_UPLOAD_SIZE_MB`
  - `422` -- empty file or undecodable image bytes

## `POST /v1/infer/video`

Asynchronous video inference; returns immediately with a job to poll.

- **Request:** `multipart/form-data`, field `file`, content-type one of
  `video/mp4`, `video/avi`, `video/quicktime`, `video/x-matroska`.
- **Response `202`:** `{"job_id": "...", "status": "queued"}`
- **Errors:** `415` unsupported content type, `413` too large, `422` empty file.
- Video duration is capped at `MAX_VIDEO_DURATION_S` (default 30s); a
  longer video causes the job to reach `status: "failed"` with an
  explanatory `error` field (not a synchronous HTTP error, since duration
  can't be known until the file is opened server-side).

## `GET /v1/jobs/{job_id}`

Poll a video job. `status` is one of `queued`, `processing`, `completed`,
`failed`.

```json
{
  "job_id": "5b2e...",
  "status": "completed",
  "error": null,
  "result": {
    "frames": [
      {"frame_index": 0, "timestamp_s": 0.0, "objects": [ { "...": "...", "track_id": 1 } ]}
    ],
    "frame_count": 5,
    "fps": 5.0,
    "total_latency_ms": 812.4,
    "model_version": "yolo:yolov8n.pt"
  }
}
```

`track_id` is stable across `frames` for the same physical object within
one video (see `docs/calibration-guide.md` and `src/threed_od/tracking.py`
for the matching algorithm and its limitations). It is always `null` for
`/v1/infer/image` since there is no second frame to track against.

- **Errors:** `404` if `job_id` is unknown or has expired
  (`JOB_RESULT_TTL_S`, default 3600s).

## Required response fields (release-gate contract)

Every detected object always includes `class_name`, `confidence`, and
`bbox`. `depth_m` and `position_3d` are `null` only in the degenerate case
of a zero-height bounding box (see `estimate_metric_depth_m` in
`calibration.py`); in normal operation they are always populated.
`track_id` is populated for video frames and `null` for single-image
inference.
