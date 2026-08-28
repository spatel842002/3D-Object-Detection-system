# Operations Runbook

## Service won't start

1. Check the startup error -- `pydantic-settings` validation errors name
   the exact offending environment variable (e.g.,
   `YOLO_CONFIDENCE_THRESHOLD must be in (0, 1]`). Fix `.env` and restart.
2. If the error is a network/download failure for model weights, confirm
   outbound network access to `github.com` (YOLOv8n weights) and
   `github.com`/PyTorch Hub mirrors (MiDaS). Weights cache under
   `~/.cache/torch/hub` and the working directory (`yolov8n.pt`); once
   cached, no network is needed to restart.

## `/health` is `200` but `/ready` shows `ready: false`

The configured `ObjectStorage` backend is unreachable.
- `STORAGE_BACKEND=s3`: confirm MinIO/S3 is up and `S3_ENDPOINT_URL`,
  `S3_ACCESS_KEY`, `S3_SECRET_KEY` are correct. `docker compose logs minio`.
- `STORAGE_BACKEND=local`: check `LOCAL_STORAGE_DIR` is writable.

## High `/v1/infer/image` latency

1. Confirm `YOLO_DEVICE`/`DEPTH_DEVICE` -- CPU inference is expected to be
   ~150-300ms/frame at 640x480 on a typical laptop CPU (see
   `docs/benchmarks/latency_results.json` for the last recorded
   environment and numbers). If you need real-time throughput, deploy the
   GPU variant (`docs/deployment.md`).
2. Check `threed_od_inference_latency_seconds` in Prometheus/Grafana for a
   trend vs. a one-off spike (cold model load on first request inflates
   the very first call only).

## A video job is stuck in `processing`

- Check server logs for `video_job_failed` (structlog); if present, the
  job's `status` will already be `failed` with an `error` message -- the
  client should re-poll and read `error`, not assume it's stuck.
- If truly stuck (process didn't crash but never advances), the video may
  be much longer than expected despite passing the upload size check --
  confirm actual frame count/fps via `ffprobe` on the source file.

## Job not found (`404` on `GET /v1/jobs/{id}`)

Jobs are evicted after `JOB_RESULT_TTL_S` (default 1 hour) or on process
restart (in-memory store -- see `docs/architecture.md`). Re-submit the
video if the job is genuinely gone.

## Rolling back a bad deploy

This service is stateless (aside from the in-memory job store, which is
inherently ephemeral). Roll back by redeploying the previous container
image tag; no database migration or data backfill is involved.

## Incident checklist

1. Check `/health` and `/ready` on the affected replica(s).
2. Check `threed_od_inference_requests_total{outcome!="success"}` for an
   error-rate spike and which `endpoint` it's on.
3. Check container logs for stack traces (`docker compose logs api` or
   `kubectl logs`).
4. Check upstream dependency health: object storage, MLflow, OTLP
   collector (a down OTLP collector should never block requests, since
   tracing export is fire-and-forget batch-exported; if it does, that's a
   bug -- file it).
5. If model-weight download is implicated (fresh deploy, cold cache),
   confirm network egress to GitHub/PyTorch Hub is not blocked by a new
   network policy.
