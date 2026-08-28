# Testing Strategy

## Layers

| Layer | Location | Needs models/network? | What it proves |
|---|---|---|---|
| Unit | `tests/unit/` | No | Calibration math, IoU tracker behavior, config validation, storage adapter correctness -- all in isolation from FastAPI and ML models. |
| Contract | `tests/contract/` | No (fake `Detector`/`DepthEstimator` doubles) | Full HTTP request/response contract: status codes, required response fields, validation/auth/not-found paths, and the real async video-job lifecycle (using a synthetic OpenCV-generated video). |
| Integration | `tests/integration/` | Yes, marked `model_download` | The *real* YOLOv8n + MiDaS_small pipeline executes end-to-end and returns a schema-valid response. Skipped automatically if network is unavailable; excluded from the default `pytest` run. |

Run everything except the network-gated integration test (this is what CI runs):

```bash
pytest -m "not model_download" --cov --cov-report=term-missing
```

Run the real-model integration test explicitly:

```bash
pytest -m model_download -v
```

## Why fake model doubles for contract tests

`tests/conftest.py` defines `FakeDetector` and `FakeDepthEstimator`
implementing the same `Detector`/`DepthEstimator` `typing.Protocol`s as
the real classes. `tests/contract/conftest.py` overrides
`app.dependency_overrides[deps.get_pipeline]` with a pipeline built from
these fakes. This means:

- The full FastAPI app, routing, validation, and error handling are
  genuinely exercised (nothing about the HTTP layer is mocked).
- CI never needs to download ~90MB of model weights or import
  `torch`/`ultralytics` for the majority of the suite, keeping it fast
  (`pytest -m "not model_download"` completes in ~2 seconds) and immune to
  upstream model-hosting flakiness.
- The one real-model test (`tests/integration/test_real_pipeline.py`)
  still exists and is run on demand (and in the release-gate checklist
  below) to prove the real wiring actually works, not just the fakes.

## Coverage

`pyproject.toml` sets `fail_under = 70` for `pytest-cov`. Actual measured
coverage on the fast suite is **82%+** (excluding `telemetry.py`'s OTLP
export path, which requires a running collector to exercise
meaningfully). Run `pytest --cov --cov-report=term-missing` to see the
exact per-file breakdown, including which lines are untested (mostly:
`YoloDetector`/`MidasDepthEstimator` real-model code paths, which are
covered instead by the integration test; and the S3 storage backend,
which is covered by contract but not by a live MinIO in the fast suite).

## Release-gate test checklist

- [ ] `ruff format --check src tests scripts`
- [ ] `ruff check src tests scripts`
- [ ] `mypy src`
- [ ] `pytest -m "not model_download" --cov` (>= 70% coverage)
- [ ] `pytest -m model_download -v` (real weights; requires network)
- [ ] `docker build -t threed-od-api .`
- [ ] `docker compose up --build` then `curl localhost:8000/health` returns `200`
- [ ] `python scripts/evaluate_latency.py` runs and writes
      `docs/benchmarks/latency_results.json`
- [ ] `python scripts/download_sample_assets.py && python scripts/run_real_demo.py ...`
      produces a real annotated image with non-empty `objects`
