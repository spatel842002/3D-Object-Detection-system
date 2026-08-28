# ADR 0003: Use Pretrained YOLOv8n and MiDaS_small, No Fine-Tuning

## Status

Accepted

## Context

The project needs a 2D detector and a monocular depth estimator. Training
either from scratch, or fine-tuning on a custom dataset, would require a
labeled dataset (with a clear, checked license), a training pipeline, GPU
time, and a real evaluation protocol -- none of which this project can
honestly claim without doing the work end-to-end, and none of which are
necessary to demonstrate the actual point of this project (combining
detection, depth, and calibration into approximate 3D localization).

## Decision

Use Ultralytics' pretrained YOLOv8n (COCO weights) and Intel ISL's
pretrained MiDaS_small, unmodified, downloaded at runtime. Report only the
upstream authors' published benchmark numbers for these models (cited in
`docs/model-card.md`), never a custom-measured accuracy claim.

## Consequences

- No dataset licensing risk from training data (none is used).
- No accuracy claim in this repository is this project's own to defend --
  clearly separates "what Ultralytics/Intel ISL measured" from "what this
  project measures" (latency, via `scripts/evaluate_latency.py`).
- Detection is limited to the 80 COCO classes; anything else is out of
  scope by construction, documented in `docs/error-analysis.md`.
- `ultralytics`'s AGPL-3.0 license applies to this dependency; see
  `docs/licenses-and-attribution.md` for the compliance analysis.

## Alternatives considered

- **Fine-tune YOLO on a custom dataset**: would require sourcing/labeling
  data and a real training+eval pipeline -- out of scope for what this
  project is demonstrating (integration of detection + depth +
  calibration, not novel model training).
