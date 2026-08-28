# ADR 0002: In-Memory Job Store for Video Inference

## Status

Accepted (with a documented scaling limitation)

## Context

Video inference on CPU can take longer than a typical HTTP request
timeout, so it needs to run asynchronously with a pollable job status.
Options ranged from a full task queue (Celery + Redis/RabbitMQ) to a
simple in-process store.

## Decision

Use FastAPI's built-in `BackgroundTasks` plus a small in-memory
`JobStore` (`src/threed_od/jobs.py`) keyed by a UUID, with TTL-based
eviction.

## Consequences

- Zero extra infrastructure (no queue/broker) is required to run the
  video-inference feature locally, keeping the project's zero-account,
  zero-paid-service local development promise.
- Job state does **not** survive a process restart and is **not** shared
  across multiple replicas -- documented in `docs/architecture.md` and
  `docs/deployment.md`, and reflected by `replicas: 1` in
  `k8s/deployment.yaml`.
- The `JobStore` interface (`create`/`get`/`mark_processing`/
  `mark_completed`/`mark_failed`) was deliberately kept narrow so a
  Redis- or database-backed implementation could be swapped in later
  without touching `api/app.py`'s route handlers.

## Alternatives considered

- **Celery + Redis**: the "correct" production answer for a
  horizontally-scaled deployment, but adds a broker dependency and
  operational complexity disproportionate to this project's scope and
  local-first goal. Noted as the natural next step if this service needed
  to scale past one replica.
