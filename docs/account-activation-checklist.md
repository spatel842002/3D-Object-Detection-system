# Account Activation Checklist

Everything in this repository runs locally today with **zero paid
accounts**: `docker compose up` brings up the API, MinIO (S3-compatible
storage), and a local MLflow server. The items below are the only
remaining steps to run this service against real hosted infrastructure,
and none of them are required for the local demo, tests, or CI to pass.

| Feature | Provider needed | Required or optional | Free tier / local alternative | Resource to create | Env vars | Verification |
|---|---|---|---|---|---|---|
| Object storage for artifacts | AWS S3 (or Azure Blob via a future adapter) | Optional | MinIO (default, already wired) | S3 bucket, e.g. `threed-od-artifacts-prod` | `STORAGE_BACKEND=s3`, `S3_ENDPOINT_URL` (omit for AWS default), `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET_NAME`, `S3_REGION`, `S3_USE_SSL=true` | `GET /ready` returns `{"ready": true, "checks": {"storage": true}}` |
| Experiment tracking at scale | Managed MLflow (e.g., Databricks-hosted, or self-hosted on a small VM with Postgres + S3 artifact store) | Optional | Local file-backed MLflow (default) | MLflow tracking server URI | `MLFLOW_TRACKING_URI` | `python scripts/evaluate_latency.py` completes and the run appears in the remote MLflow UI |
| Distributed tracing backend | Datadog, Azure Monitor / Application Insights, Honeycomb, or any OTLP-compatible backend | Optional | Disabled by default (no-op) | An OTLP ingestion endpoint + API key per provider's docs | `OTEL_EXPORTER_OTLP_ENDPOINT` | Traces appear in the provider's UI after an inference request |
| GPU inference | AWS EC2 (`g4dn.xlarge`+) or any GPU host | Optional (only for real-time throughput) | CPU mode (default) | A GPU instance with NVIDIA drivers + Container Toolkit | `YOLO_DEVICE=cuda`, `DEPTH_DEVICE=cuda` | `docker run --gpus all ...` then a sub-100ms `/v1/infer/image` latency (see `docs/deployment.md`) |
| Kubernetes deployment | Any managed Kubernetes (EKS/AKS/GKE) or self-hosted cluster | Optional | `kind`/`k3d` locally | A cluster + container registry to push `threed-od-api` to | Image reference in `k8s/deployment.yaml`; secrets via `k8s/secret.example.yaml` | `kubectl get pods` shows `Running`, `kubectl port-forward` + `curl /health` returns `200` |
| Container registry | Docker Hub, GitHub Container Registry, ECR, or ACR | Required only for a real Kubernetes deployment | N/A (local `docker build` is sufficient for local Docker/Compose use) | A repository, e.g. `ghcr.io/spatel842002/threed-od-api` | N/A (image reference in manifests/CI, not an app env var) | `docker push` succeeds; `kubectl` can pull the image |

## IAM / least-privilege notes (if using real AWS S3)

The service only needs: `s3:GetObject`, `s3:PutObject`, `s3:ListBucket`,
and `s3:CreateBucket`/`s3:HeadBucket` (bucket auto-bootstrap) scoped to
the single bucket named above. No other AWS permissions are required by
this codebase.

## Cost risk and cleanup

- MinIO, local MLflow, `kind`/`k3d`: **$0**, entirely local.
- AWS S3: negligible for demo-scale traffic; delete the bucket
  (`aws s3 rb s3://<bucket> --force`) when done.
- GPU EC2 instance: **billed hourly while running** -- stop or terminate
  the instance immediately after any demo/benchmark session
  (`aws ec2 terminate-instances --instance-ids <id>`).
- Managed Kubernetes (EKS/AKS/GKE): billed for the control plane and
  worker nodes continuously while the cluster exists -- destroy the
  cluster when not actively demoing it.

No resource in this checklist is created automatically by any script in
this repository; every item above is a manual, account-owner action.
