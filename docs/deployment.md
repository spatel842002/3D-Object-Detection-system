# Deployment

## CPU (default)

```bash
docker build -t threed-od-api .
docker run -p 8000:8000 threed-od-api
```

Uses `python:3.11-slim` + CPU-only PyTorch wheels
(`--index-url https://download.pytorch.org/whl/cpu`). Suitable for the
local demo and low-throughput deployments; see
`docs/benchmarks/latency_results.json` for measured CPU latency.

## GPU / EC2 deployment mode

Not built or tested in this environment (no GPU available here), but
wired for it:

1. Build from a CUDA-enabled base image instead of `python:3.11-slim`,
   e.g. `nvidia/cuda:12.4.1-runtime-ubuntu22.04`, installing Python 3.11
   and the default (non-`+cpu`) `torch==2.9.1`/`torchvision==0.24.1`
   wheels from PyPI, which include CUDA support.
2. Set `YOLO_DEVICE=cuda` and `DEPTH_DEVICE=cuda`.
3. On EC2, use a `g4dn.xlarge` or larger GPU instance with the NVIDIA
   Container Toolkit installed, and run the container with
   `docker run --gpus all ...`.
4. Everything else (API contract, storage adapters, MLflow, metrics) is
   identical between CPU and GPU modes -- only the base image and the two
   device environment variables change.

This is documented rather than provisioned because standing up a real GPU
instance requires an AWS account and incurs cost, which this project's
development process intentionally defers to
`docs/account-activation-checklist.md`.

## Kubernetes (reference manifests)

`k8s/deployment.yaml`, `k8s/service.yaml`, `k8s/configmap.yaml`, and
`k8s/secret.example.yaml` define a basic Deployment + Service + ConfigMap
+ Secret template. They were authored against the standard `apps/v1`
Deployment and `v1` Service/ConfigMap/Secret schemas and validated for
YAML syntax; **full `kubectl apply --dry-run=client` schema validation
against a live cluster (`kind`/`k3d`) was not run in this development
environment because neither tool is installed here** -- see
`SHRIYA_PORTFOLIO_BUILD_STATUS.md` in the parent workspace for this
documented gap. To validate before a real deployment:

```bash
kind create cluster
kubectl apply --dry-run=client -f k8s/
kubectl apply -f k8s/
kubectl port-forward svc/threed-od-api 8000:80
```

Note `replicas: 1` in `k8s/deployment.yaml` is intentional: the in-memory
`JobStore` (see `docs/architecture.md`) does not work correctly across
multiple replicas behind one Service today. Scale beyond 1 replica only
after replacing `JobStore` with a shared backend.

## Terraform / cloud infrastructure

Not provided for this specific project: this service has no
infrastructure dependency beyond a container runtime, an S3-compatible
bucket, and (optionally) a hosted MLflow/OTLP endpoint, all of which are
covered by environment variables rather than project-specific IaC. See
`docs/account-activation-checklist.md` for the exact hosted resources and
their configuration if you choose to deploy this to a cloud account.
