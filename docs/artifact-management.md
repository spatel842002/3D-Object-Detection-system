# Artifact Management

## Model weights

Not versioned by this project's own tooling -- they are pinned by the
upstream package/hub reference (`YOLO_WEIGHTS=yolov8n.pt`,
`DEPTH_MODEL_NAME=MiDaS_small`), which Ultralytics/`torch.hub` resolve to
a specific published release. To pin to a different upstream version,
change these environment variables; there is no local model registry in
this project (that would be over-engineering for two unmodified,
pretrained weights).

## MLflow (benchmark run tracking)

- **Local default:** file-backed store at `mlruns/` (gitignored),
  configured via `MLFLOW_TRACKING_URI=file:./mlruns`.
- **What's logged:** `scripts/evaluate_latency.py` logs benchmark
  parameters (resolution, device, model versions, platform) and latency
  metrics (mean/p50/p95/min/max) per run, plus the
  `docs/benchmarks/latency_results.json` file as an artifact.
- **Production:** point `MLFLOW_TRACKING_URI` at a remote MLflow server
  (e.g., one backed by a managed Postgres + S3 artifact store) -- no code
  change required, since the tracking URI is the only thing that changes.
  See `docs/account-activation-checklist.md`.

## Object storage (MinIO / S3)

- **Local default:** MinIO container via `docker-compose.yml`, bucket
  `threed-od-artifacts` auto-created on first use
  (`S3CompatibleStorage._ensure_bucket`).
- **Tests:** `LocalFilesystemStorage` (a temp directory) is used instead,
  so the fast test suite never needs a running MinIO.
- **Production:** set `STORAGE_BACKEND=s3`, `S3_ENDPOINT_URL` to your AWS
  region endpoint (or omit for the default AWS endpoint resolution),
  and real IAM-scoped credentials -- never the `minioadmin` defaults.

## What is NOT committed to this repository

- Model weight files (`*.pt`, `*.pth`, `*.onnx`) -- gitignored.
- `mlruns/`/`mlartifacts/` (local MLflow data) -- gitignored.
- `data/` (sample images, demo output artifacts) -- gitignored, except the
  specific, small, licensed screenshots intentionally copied into
  `docs/assets/screenshots/` for documentation (see
  `docs/reproducible-sample-output.md` for exactly how those were
  produced and their license/attribution).
