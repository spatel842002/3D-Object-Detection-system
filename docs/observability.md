# Observability

## Metrics (Prometheus)

Exposed at `GET /metrics` in Prometheus exposition format
(`src/threed_od/telemetry.py`):

| Metric | Type | Labels | Meaning |
|---|---|---|---|
| `threed_od_inference_requests_total` | Counter | `endpoint`, `outcome` (`success`/`rejected`/`invalid`/`failed`) | Request outcomes per endpoint. |
| `threed_od_inference_latency_seconds` | Histogram | `endpoint` | End-to-end pipeline latency. |
| `threed_od_detected_objects_total` | Counter | `class_name` | Count of detected objects by COCO class, useful for drift/volume dashboards. |

Local Prometheus scrape config: `deploy/prometheus.yml`. Start with the
observability profile:

```bash
docker compose --profile observability up --build
# Prometheus: http://localhost:9090
# Grafana:    http://localhost:3000 (admin/admin)
```

### Suggested Grafana panels

- P50/P95/P99 of `threed_od_inference_latency_seconds` by `endpoint`.
- Error rate: `rate(threed_od_inference_requests_total{outcome!="success"}[5m])`.
- Detected-object volume by class over time, to spot dataset/domain drift.

## Tracing (OpenTelemetry, optional)

`configure_tracing()` in `telemetry.py` is a no-op unless
`OTEL_EXPORTER_OTLP_ENDPOINT` is set, so the service has zero tracing
overhead/dependency by default. When set, spans are exported via OTLP/gRPC
-- point it at the local `otel-collector` service (`deploy/otel-collector-config.yaml`)
or a hosted backend (Datadog agent, Azure Monitor OTLP ingestion, etc.).

## Structured logging

`structlog` is configured in `api/app.py`; the video-processing background
task logs `video_job_failed` with `job_id` and `error` on failure. There is
currently no per-request correlation ID middleware -- see
`docs/troubleshooting.md` for how to correlate a client report with server
logs today (job_id for video; none yet for synchronous image requests,
noted as a limitation).

## Health vs. readiness

- `/health`: process liveness only; never touches models. Reports whether
  the detector/depth model have been *lazily loaded yet* (informational,
  not a failure condition -- both load on first inference request).
- `/ready`: verifies the configured object-storage backend is reachable.
  Returns `200` with `ready: false` (not a `5xx`) if a dependency check
  fails, so orchestrators can distinguish "process is up but not ready"
  from "process crashed."
