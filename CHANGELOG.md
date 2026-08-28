# Changelog

All notable changes to this project are documented here. Format based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Initial working implementation: FastAPI inference service combining a
  pretrained YOLOv8n detector, MiDaS_small monocular depth estimation, an
  IoU-based multi-object tracker, and a pinhole-camera + similarity-triangle
  calibration model for approximate 3D localization.
- Synchronous `/v1/infer/image` and asynchronous job-based
  `/v1/infer/video` endpoints, plus `/health`, `/ready`, and `/metrics`.
- S3-compatible object storage adapter (MinIO locally, AWS S3 in
  production) with a local-filesystem fallback for tests.
- Local MLflow experiment tracking for latency benchmarks.
- Prometheus metrics and optional OpenTelemetry OTLP trace export.
- Unit, contract, and (optional, network-gated) real-model integration
  test suites.
- Docker CPU image, Docker Compose stack (API + MinIO + MLflow, with an
  optional observability profile), and GitHub Actions CI.
- Baseline documentation set under `docs/` (architecture, model card,
  dataset card, calibration guide, API, security, deployment,
  observability, runbook, troubleshooting, environment variables,
  account-activation checklist).
