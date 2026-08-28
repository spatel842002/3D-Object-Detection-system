# Deployment View

## Local (Docker Compose)

```mermaid
graph LR
    Dev[Developer / curl / browser] -->|:8000| API[threed-od-api container]
    API -->|S3 API :9000| MinIO[(MinIO)]
    API -->|tracking API :5000| MLflow[(MLflow server)]
    API -.optional profile.-> Otel[OTel Collector] --> Prom[Prometheus] --> Graf[Grafana]
```

Started with `docker compose up --build` (core stack) or
`docker compose --profile observability up --build` (adds tracing/metrics
dashboards). See `docs/local-development.md`.

## Kubernetes (reference)

```mermaid
graph LR
    Ingress -->|/*, :80| Svc[Service: threed-od-api]
    Svc --> Pod1[Pod: threed-od-api]
    Svc --> Pod2[Pod: threed-od-api]
    Pod1 -->|/health /ready| Kubelet1[kubelet probes]
    Pod2 -->|/health /ready| Kubelet2[kubelet probes]
    Pod1 --> S3[(External S3-compatible bucket)]
    Pod1 --> MLflowSvc[(MLflow tracking service)]
```

Manifests are in `k8s/` and were authored against `kind`/`k3d` for local
validation (`kubectl apply --dry-run=client` and `kubectl apply -f k8s/`
against a local cluster); see `docs/deployment.md` for exact commands and
`docs/account-activation-checklist.md` for the EKS/AKS-specific overlay
inputs (image registry, IAM role, ingress class) that are account-only.

Because the job store is in-memory and per-pod, `replicas > 1` means a
video-inference job's status is only visible from the pod that accepted
it. `docs/architecture.md` documents the Redis/DB-backed `JobStore`
replacement needed before running multiple replicas behind a
round-robin Service in production.
