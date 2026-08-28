# Error Analysis / Known Failure Modes

This project does not have access to ground-truth 3D position data (no
LiDAR/stereo rig), so this document is a structured, honest account of
*where and why* errors are expected by construction, rather than a
measured error table.

## Detection-stage errors (inherited from YOLOv8n)

- Small or heavily occluded objects are missed below the confidence
  threshold (`YOLO_CONFIDENCE_THRESHOLD`, default 0.35).
- Only the 80 COCO classes are recognized; anything else is silently not
  detected (no "unknown object" class).
- Confusable classes (e.g., "cat" vs. "dog" at low resolution) will
  occasionally be mislabeled, which directly corrupts the depth estimate
  for that object since the label selects which typical-height row is
  used (see `docs/calibration-guide.md`).

## Depth-stage errors (by construction of the similarity-triangle heuristic)

| Scenario | Effect on reported depth |
|---|---|
| Object is a child, not an adult (class "person") | Overestimated depth (bbox looks "too small for an adult") |
| Object is partially cropped by the frame edge | Underestimated depth (bbox height understates true height) |
| Object is lying down / not oriented per the table assumption | Estimate is meaningless for that frame |
| `CAMERA_FOCAL_LENGTH_PX` doesn't match the actual camera | Every depth in the frame is wrong by the same multiplicative factor |
| Object is unknown class, falls back to `DEPTH_REFERENCE_OBJECT_HEIGHT_M` | Error magnitude depends on how far the true object size is from 1.7m |

## Tracking-stage errors

`IouTracker` is a greedy IoU matcher with no motion model
(`tracking.py`). Expected failure modes:
- **ID switches** when two same-class objects cross paths or overlap
  heavily between frames.
- **New ID assigned** after an object is occluded for more than
  `max_frames_missing` (default 5) consecutive frames, even though it's
  the "same" object reappearing.
- Fast camera motion or low frame rate reduces inter-frame IoU below
  `iou_threshold` (default 0.3), causing spurious new track IDs.

## What would reduce these errors (not implemented here, by design)

- A calibrated depth sensor or stereo pair for ground-truth metric depth.
- A Kalman-filter-based tracker (e.g., SORT/DeepSORT) with a motion model.
- Per-deployment camera calibration instead of the KITTI-derived default
  focal length.
- Fine-tuning YOLO on a domain-specific dataset if the target objects
  differ significantly from COCO's distribution.

These are called out explicitly rather than silently working around them,
per this project's truthfulness constraints (see `AGENTS.md`).
