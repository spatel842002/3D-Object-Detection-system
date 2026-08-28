# Calibration Guide: How "3D" Actually Works Here

This document exists because monocular (single-camera) 3D localization is
easy to overstate. Read this before trusting or presenting any distance
number this service returns.

## The problem

A single 2D image has no depth information by itself. To report an
approximate `(x, y, z)` position for a detected object, this project
combines three independent, approximate pieces:

1. **2D detection** (YOLOv8n): a pixel bounding box + class label.
2. **A camera model** (pinhole projection): converts pixels + an assumed
   depth into a 3D ray.
3. **A depth estimate**: the missing piece that turns "somewhere along
   this ray" into an actual point.

## How depth is estimated here

We do **not** use MiDaS's output as the metric depth number, because
MiDaS produces *relative, unitless* inverse depth -- correct for "is pixel
A closer than pixel B", not for "pixel A is 8.2 meters away". Recovering
true metric scale from a single MiDaS pass, with no calibration target,
second camera, or IMU, is an open research problem, not something we
gloss over.

Instead, `estimate_metric_depth_m` in `src/threed_od/calibration.py` uses
the classic **similarity-triangle heuristic**, which is what allows this
project to report a metric number without a calibrated rig:

```
depth_m = (typical_real_world_height_m * focal_length_px) / bbox_height_px
```

This is the same geometry used by "distance to object" tools going back
decades: a farther object of the same real size subtends fewer pixels.
`TYPICAL_OBJECT_HEIGHTS_M` holds a small table of average real-world
heights per COCO class (e.g., `person: 1.70`, `car: 1.50`). Unknown
classes fall back to `DEPTH_REFERENCE_OBJECT_HEIGHT_M` (default 1.7m).

### Error sources (be explicit about these)

| Source | Effect |
|---|---|
| Object's real size differs from the table average (a child, a compact vs. a truck-class "car", a toy) | Depth is wrong proportionally to the size mismatch |
| Partial occlusion (bbox height is smaller than the true object height) | Depth is under-estimated (looks closer than it is) |
| Wrong/uncalibrated `CAMERA_FOCAL_LENGTH_PX` | Depth is wrong by the same ratio as the focal-length error |
| Object not upright / viewed at an angle | Height-based heuristic breaks down |

This is a documented approximation suitable for a demo/portfolio project,
not a calibrated measurement device. It should never be presented as
survey-grade or safety-critical.

## Camera intrinsics

`CameraIntrinsics` (pinhole model) needs a focal length in pixels and a
principal point (defaults to the image center if not supplied). The
default `CAMERA_FOCAL_LENGTH_PX=721.5` is the commonly cited focal length
from the KITTI dataset's left color camera at its native resolution -- a
reasonable "typical webcam/dashcam-ish" starting point, **not** a
calibration of any specific camera you plug in. For accurate results
against a real camera, calibrate it (e.g., OpenCV's checkerboard
`cv2.calibrateCamera` routine) and set `CAMERA_FOCAL_LENGTH_PX`,
`CAMERA_PRINCIPAL_POINT_X`, and `CAMERA_PRINCIPAL_POINT_Y` from that
result.

## Back-projection

Given a bounding-box center `(u, v)` and the estimated depth `Z`:

```
X = (u - cx) * Z / f
Y = (v - cy) * Z / f
```

This is standard pinhole back-projection (see `pixel_to_3d` in
`calibration.py`), producing a camera-relative position in meters:
`+X` right, `+Y` down (image convention), `+Z` forward.

## What this system is not

- Not stereo vision, not LiDAR, not structure-from-motion.
- Not a substitute for a calibrated depth sensor in any safety-relevant
  application.
- MiDaS's relative depth map is currently exposed only inside the
  pipeline (`DetectionPipeline.run_on_image` computes it) and is not yet
  surfaced as a full per-pixel map in the API response; only the
  per-object metric estimate is returned today.
