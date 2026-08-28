# ADR 0001: Similarity-Triangle Heuristic for Metric Depth

## Status

Accepted

## Context

The project needs to report an approximate metric (meters) distance to
each detected object using only a single RGB camera, with no stereo pair,
LiDAR, or IMU available. A monocular depth network (MiDaS) was already
planned for scene-relative depth, but MiDaS's output is relative,
unitless inverse depth -- it cannot, by itself, be converted to meters
without an external metric reference.

## Decision

Use the classic similarity-triangle heuristic
(`depth_m = typical_real_height_m * focal_length_px / bbox_height_px`)
per detected object, keyed by COCO class, as the source of the metric
depth reported in the API. MiDaS is retained in the pipeline for its
relative depth map (useful scaffolding for future frame-level reasoning)
but is not the source of the metric number today.

## Consequences

- Metric depth accuracy is bounded by how close a detected instance's
  real size is to the table's typical value -- documented explicitly in
  `docs/calibration-guide.md` and `docs/error-analysis.md`.
- No training data, calibration rig, or per-deployment calibration step is
  required to get *a* metric number, which fits this project's
  local-first, zero-account-required development constraint.
- If a future iteration adds a real depth sensor or stereo pair, this
  heuristic should be replaced (or used only as a fallback) -- the
  `calibration.py` module's functions are intentionally small and
  independent of the rest of the pipeline so that swap is localized.

## Alternatives considered

- **Trust MiDaS's raw output as metric**: rejected -- it is not metric by
  construction; presenting it as such would violate this project's
  truthfulness constraints.
- **Require a calibration target (checkerboard) per deployment**: more
  accurate, but adds friction incompatible with a zero-setup local demo;
  documented as the recommended real-camera improvement instead of the
  default.
