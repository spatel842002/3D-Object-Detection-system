# Privacy and Responsible Use

## What this system is

A demonstration/portfolio inference service that detects common objects
(COCO's 80 classes) in an image or video and estimates an approximate
distance and 3D position using the heuristics documented in
`docs/calibration-guide.md`. It is not a certified measurement device.

## What this system must not be used for

- **Not for identifying or tracking specific people.** YOLOv8n detects
  the generic class `"person"`; it performs no face recognition, no
  re-identification across sessions, and this project adds none. The
  `track_id` produced by `IouTracker` is only stable *within a single
  video processing job* and carries no identity information.
- **Not for safety-critical distance measurement.** Do not use the
  `depth_m`/`position_3d` fields for collision avoidance, autonomous
  navigation, or any application where an incorrect distance estimate
  could cause physical harm. See `docs/error-analysis.md` for why these
  numbers can be meaningfully wrong.
- **Not for automated enforcement or access control** (e.g., automatically
  flagging/penalizing people based on detected position or presence).
- **Not for surveillance of individuals without their knowledge/consent**
  where applicable law or policy requires it. Deployers, not this
  library, are responsible for lawful use of any footage they process.

## Data handling

- Uploaded images are processed in memory and discarded after the
  response is returned; nothing is written to disk.
- Uploaded videos are written to a temp file for the duration of
  processing and deleted immediately after (success or failure) --
  see `_process_video_job`'s `finally` block in `src/threed_od/api/app.py`.
- Nothing is sent to a third party by default. Object storage, if
  configured (`STORAGE_BACKEND=s3`), is self-hosted (MinIO) locally or
  whatever S3-compatible bucket the operator configures; this project's
  code does not upload inference inputs anywhere unless a caller
  explicitly does so.
- No telemetry about image *content* is exported -- only aggregate,
  non-identifying metrics (counts by class name, latency histograms; see
  `docs/observability.md`).

## Sample media used in this repository's own documentation

The one demo photo used to produce `docs/assets/screenshots/` was sourced
from Wikimedia Commons under a CC BY 2.0 license (a public street scene,
already published; see `THIRD_PARTY_NOTICES.md` for full attribution). No
photo containing a private individual outside a public setting, and no
government ID or similarly sensitive image, is used anywhere in this
project.
