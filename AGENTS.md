# AGENTS.md

Instructions for any AI coding agent (or human) working in this
repository.

## What this project actually is

A FastAPI service that combines a pretrained YOLOv8n detector, a
pretrained MiDaS_small monocular depth model, an IoU tracker, and a
pinhole-camera + similarity-triangle calibration heuristic to return
approximate 3D object positions from images/video. It does **not** train
or fine-tune any model. Read `docs/model-card.md` and
`docs/calibration-guide.md` before changing anything depth- or
detection-related.

## Truthfulness constraints (do not violate these)

- Never claim this project trained, fine-tuned, or achieved a custom
  accuracy number for YOLOv8n or MiDaS. Cite upstream published
  benchmarks explicitly if referencing accuracy at all (see
  `docs/model-card.md`).
- Never present the reported `depth_m`/`position_3d` as calibrated,
  survey-grade, or safety-critical. It is a documented heuristic (see
  `docs/calibration-guide.md`, `docs/error-analysis.md`).
- Never commit model weight files, datasets, real personal photos, or
  secrets. `data/`, `mlruns/`, `*.pt`/`*.pth` are gitignored -- keep them
  that way.
- Any sample media added to the repo must have a checked, compatible
  license recorded in `THIRD_PARTY_NOTICES.md` (see the CC BY 2.0
  Wikimedia Commons photo already used as the precedent).
- Do not weaken `pyproject.toml`'s `fail_under` coverage threshold, mypy
  strictness, or CI checks just to make a build pass -- fix the root
  cause.

## Commands

```bash
# setup
python -m venv .venv && .venv/Scripts/activate
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.9.1 torchvision==0.24.1
pip install -e ".[dev]"

# fast checks (what CI runs)
ruff format --check src tests scripts
ruff check src tests scripts
mypy src
pytest -m "not model_download" --cov --cov-report=term-missing

# real-model check (network required, not in CI's default gate)
pytest -m model_download -v

# run it
uvicorn threed_od.main:app --reload
docker compose up --build
```

## Architecture boundaries

- `detection.py` / `depth.py` / `storage.py` expose `typing.Protocol`
  interfaces (`Detector`, `DepthEstimator`, `ObjectStorage`). New
  implementations (a different model, a different storage backend) should
  implement these protocols rather than changing `pipeline.py` or
  `api/app.py`.
- `pipeline.py` has no FastAPI or HTTP knowledge -- it operates on numpy
  arrays and returns typed `schemas.py` objects. Keep it that way so it
  stays testable without spinning up the API.
- `api/deps.py` is the only place real models/storage/job-store are
  constructed (as `lru_cache` singletons). Tests override these via
  `app.dependency_overrides`, never by monkeypatching internals.
- Settings (`config.py`) are the single source of environment
  configuration; don't read `os.environ` directly elsewhere.

## Release gate (must all pass before considering a change "done")

See `docs/testing.md`'s "Release-gate test checklist" for the full list:
format, lint, type check, fast test suite with coverage, the real-model
integration test, a Docker build, `docker compose up` health check, the
latency benchmark script, and the real-demo script producing a non-empty
detection result.
