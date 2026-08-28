# Local Development

## One-command bootstrap (no Docker)

```bash
python -m venv .venv
.venv/Scripts/activate                # macOS/Linux: source .venv/bin/activate
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.9.1 torchvision==0.24.1
pip install -e ".[dev]"
pytest -m "not model_download"        # fast suite, no model downloads, no GPU
uvicorn threed_od.main:app --reload
```

The service starts with **zero required configuration** -- every setting
in `src/threed_od/config.py` has a safe local default (`STORAGE_BACKEND=local`,
CPU inference, file-based MLflow, no OTLP export). Copy `.env.example` to
`.env` only if you want to override something.

First real inference request downloads YOLOv8n (~6MB) and MiDaS_small
(~82MB) automatically; subsequent requests use the cached weights.

## Docker Compose (full stack: API + MinIO + MLflow)

```bash
docker compose up --build
# API:        http://localhost:8000/docs
# MinIO console: http://localhost:9001 (minioadmin/minioadmin)
# MLflow UI:  http://localhost:5001
```

Add the observability profile for Prometheus/Grafana/OTel Collector:

```bash
docker compose --profile observability up --build
```

## Common tasks

| Task | Command |
|---|---|
| Format | `ruff format src tests scripts` |
| Lint | `ruff check src tests scripts` |
| Type check | `mypy src` |
| Fast tests + coverage | `pytest -m "not model_download" --cov --cov-report=term-missing` |
| Real-model integration test | `pytest -m model_download -v` |
| Latency benchmark | `python scripts/evaluate_latency.py` |
| Real demo on a real photo | `python scripts/download_sample_assets.py && python scripts/run_real_demo.py data/samples/street_scene_sample.jpg` |
| Regenerate lockfile | `pip freeze --exclude-editable > requirements.txt` |

## Project layout

```
src/threed_od/
  config.py        # env-driven settings, validated at startup
  schemas.py        # pydantic API contracts
  detection.py       # YoloDetector (Ultralytics YOLOv8n)
  depth.py           # MidasDepthEstimator (MiDaS_small via torch.hub)
  calibration.py     # pinhole camera model + metric-depth heuristic
  tracking.py         # IoU-based multi-object tracker
  pipeline.py         # wires detection+depth+calibration together
  storage.py           # local filesystem / S3-compatible object storage
  jobs.py               # in-memory async job store (video inference)
  telemetry.py           # Prometheus metrics + optional OTel tracing
  api/
    app.py                # FastAPI routes
    deps.py                # lazily-constructed singletons (models, storage, jobs)
scripts/                # latency benchmark, real demo, sample-asset downloader
tests/{unit,contract,integration}/
docs/                    # this documentation set
k8s/                     # reference Kubernetes manifests
deploy/                  # Prometheus/OTel Collector local configs
```
