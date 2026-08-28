# Evaluation Methodology

## What this project measures itself, and what it cites

| Metric | Who measures it | How |
|---|---|---|
| Detection mAP, precision/recall | **Cited from Ultralytics' published benchmarks** | Not reproduced locally; see `docs/model-card.md` for the citation and why (avoids requiring a ~1GB COCO download for the release gate). |
| Depth-estimate quality | **Documented as a heuristic with known error sources** | No ground-truth LiDAR/stereo rig is available to this project, so quantitative depth error (e.g., MAE in meters) is not claimed. `docs/calibration-guide.md` and `docs/error-analysis.md` describe the error sources qualitatively and by construction. |
| End-to-end pipeline latency | **This project, reproducibly** | `scripts/evaluate_latency.py` |

## Latency benchmark methodology

`scripts/evaluate_latency.py`:

1. Loads the real `YoloDetector` + `MidasDepthEstimator` on CPU.
2. Generates a deterministic synthetic frame (`numpy` `default_rng(seed=42)`)
   at a configurable resolution (default 640x480).
3. Runs `--warmup` (default 3) untimed iterations to exclude model-load /
   first-inference JIT effects.
4. Times `--runs` (default 20) iterations of
   `DetectionPipeline.run_on_image` end-to-end (detection + depth +
   calibration), recording wall-clock latency per run.
5. Reports mean, p50, p95, min, max, and the exact platform/processor the
   run happened on.
6. Writes `docs/benchmarks/latency_results.json` and logs the same
   params/metrics to the local MLflow tracking server
   (`MLFLOW_TRACKING_URI`), so results are versioned per run, not just
   overwritten prose in a README.

Reproduce with:

```bash
python scripts/evaluate_latency.py --runs 20 --resolution 640x480
```

Numbers vary by CPU; the committed `docs/benchmarks/latency_results.json`
records the exact environment (`platform.platform()`,
`platform.processor()`, Python version) alongside the numbers so results
are not presented out of context.

## Why a synthetic frame, not a real photo, for latency

Latency (unlike accuracy) does not depend on image *content*, only on
resolution and model architecture, so a synthetic frame keeps the
benchmark fully offline and reproducible without a network dependency.
Detection *quality* on a real photo is demonstrated separately via
`scripts/run_real_demo.py` against a properly licensed sample image (see
`docs/reproducible-sample-output.md`).

## Test-suite validation strategy

- **Unit tests** (`tests/unit/`) validate calibration math, tracker
  behavior, config validation, and storage adapters without loading any
  ML model.
- **Contract tests** (`tests/contract/`) validate the full FastAPI
  request/response contract (status codes, required fields, error paths)
  using injected fake `Detector`/`DepthEstimator` doubles -- fast, and CI
  never needs network access or GPU/CPU-heavy model downloads for these.
- **Integration test** (`tests/integration/test_real_pipeline.py`,
  `pytest -m model_download`) loads the *real* YOLOv8n + MiDaS_small
  weights and proves the real pipeline executes end-to-end and returns a
  schema-valid response. It is network-gated and skipped automatically if
  no network is available; it is excluded from the default `pytest` run
  and from the required CI gate (which uses `-m "not model_download"`) so
  CI does not depend on flaky external downloads, but is documented and
  runnable on demand.
