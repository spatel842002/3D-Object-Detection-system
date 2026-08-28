# Model Card

## Summary

This project does not train any custom detection or depth model. It
composes two pretrained, unmodified open-source models:

| Component | Model | Weights | Task |
|---|---|---|---|
| 2D detection | YOLOv8n (Ultralytics) | `yolov8n.pt`, COCO-pretrained, auto-downloaded | 80-class 2D bounding-box detection |
| Monocular depth | MiDaS_small (Intel ISL) | auto-downloaded via `torch.hub` | Relative, unitless inverse-depth map |

No accuracy numbers in this repository are claimed as this project's own;
where accuracy is discussed below it is the upstream authors' published
benchmark, cited explicitly.

## Intended use

Portfolio/demonstration inference service for combining 2D detection with
approximate monocular depth to produce a rough 3D position estimate. It is
**not** validated for safety-critical use (e.g., autonomous vehicles,
robotics collision avoidance, medical, or security screening).

## YOLOv8n detection

- Pretrained on COCO (80 classes; see
  `TYPICAL_OBJECT_HEIGHTS_M` in `src/threed_od/calibration.py` for the
  subset this project attaches a depth-heuristic height to).
- Published upstream benchmark (COCO val2017, from the
  [Ultralytics YOLOv8 documentation](https://docs.ultralytics.com/models/yolov8/)):
  YOLOv8n reports **37.3 mAP@0.5:0.95** at 640px input, ~80 layers, ~3.2M
  parameters, and Ultralytics-reported CPU ONNX latency of roughly 80ms per
  image on their reference hardware. These are the upstream authors'
  numbers, not reproduced by this repository -- reproducing a full COCO
  val2017 mAP run would require downloading the ~1GB COCO validation set,
  which this project intentionally does not bundle or require for its
  release gate.
- This project's own `scripts/evaluate_latency.py` measures **this
  pipeline's** end-to-end wall-clock latency (detection + depth +
  calibration) on the actual machine it's run on; see
  `docs/benchmarks/latency_results.json` after running it, and
  `docs/evaluation-methodology.md`.

## MiDaS_small depth

- Outputs relative, unitless inverse depth -- **not metric**. It is
  primarily used in this project as available scaffolding for
  frame-level depth reasoning; the per-object *metric* depth reported by
  the API comes from the similarity-triangle heuristic in
  `calibration.py`, not from MiDaS directly. See
  `docs/calibration-guide.md` for exactly how the two combine and why.
- Upstream repository: [isl-org/MiDaS](https://github.com/isl-org/MiDaS).

## Known limitations and failure modes

See `docs/error-analysis.md` for a fuller treatment. In summary:

- Metric depth accuracy depends entirely on how close a detected object's
  real size is to the assumed typical size in
  `TYPICAL_OBJECT_HEIGHTS_M` -- a child, a compact car, or a partially
  occluded object will have proportionally wrong estimated depth.
  There is no LiDAR, stereo, or IMU input to correct this.
- No custom fine-tuning was performed, so class coverage is limited to
  COCO's 80 classes.
- The IoU tracker (`tracking.py`) has no motion model; fast motion, heavy
  occlusion, or camera shake will cause track ID switches.
- CPU inference latency (see benchmark) makes this unsuitable for
  real-time (>10fps) use without a GPU.

## Responsible use

Do not present this system's distance estimates as survey-grade,
safety-critical, or suitable for automated decision-making that affects
people (e.g., automated enforcement, access control). See
`docs/privacy-and-responsible-use.md`.
