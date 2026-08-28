"""Camera calibration and monocular metric-depth approximation.

Design (see docs/calibration-guide.md for the full write-up and error
bounds):

1. YOLO gives a 2D bounding box in pixels.
2. A monocular depth network (MiDaS) gives *relative*, unitless
   inverse-depth ordering across the frame -- it is NOT metric and is used
   only to rank objects front-to-back within a single frame.
3. Absolute metric depth per object is approximated with the classic
   similarity-triangle heuristic: depth = (real_world_height * focal_length)
   / apparent_height_in_pixels, using a table of typical real-world object
   heights per COCO class. This is a well-understood approximation, not a
   calibrated measurement, and its error grows for objects that deviate
   from the assumed typical size (e.g., a child vs. an adult "person").
4. The pinhole camera model then back-projects (u, v, depth) into an
   approximate camera-relative (X, Y, Z) position.

Nothing here should be presented as survey-grade or safety-critical
distance measurement.
"""

from __future__ import annotations

from dataclasses import dataclass

from .schemas import BoundingBox, Point3D

# Typical real-world object heights in meters, used only for the monocular
# metric-depth approximation described above. Values are rough population
# averages, not per-instance ground truth.
TYPICAL_OBJECT_HEIGHTS_M: dict[str, float] = {
    "person": 1.70,
    "bicycle": 1.10,
    "car": 1.50,
    "motorcycle": 1.20,
    "airplane": 6.00,
    "bus": 3.20,
    "train": 3.80,
    "truck": 3.00,
    "boat": 1.80,
    "traffic light": 0.90,
    "fire hydrant": 0.75,
    "stop sign": 0.75,
    "bench": 0.80,
    "dog": 0.55,
    "cat": 0.30,
    "horse": 1.60,
    "cow": 1.40,
    "chair": 0.90,
    "couch": 0.85,
    "potted plant": 0.60,
    "dining table": 0.75,
    "tv": 0.55,
    "laptop": 0.25,
    "suitcase": 0.60,
}


@dataclass(frozen=True)
class CameraIntrinsics:
    """Pinhole camera intrinsic parameters, in pixels."""

    focal_length_px: float
    principal_point_x: float
    principal_point_y: float

    @classmethod
    def from_image_size(
        cls,
        image_width: int,
        image_height: int,
        focal_length_px: float,
        principal_point_x: float | None = None,
        principal_point_y: float | None = None,
    ) -> CameraIntrinsics:
        """Build intrinsics, defaulting the principal point to the image center."""
        return cls(
            focal_length_px=focal_length_px,
            principal_point_x=principal_point_x
            if principal_point_x is not None
            else image_width / 2.0,
            principal_point_y=principal_point_y
            if principal_point_y is not None
            else image_height / 2.0,
        )


def estimate_metric_depth_m(
    class_name: str,
    bbox: BoundingBox,
    focal_length_px: float,
    default_height_m: float,
) -> float | None:
    """Approximate metric depth to an object using the similarity-triangle heuristic.

    Returns None if the bounding box has non-positive height (degenerate detection).
    """
    bbox_height_px = bbox.y_max - bbox.y_min
    if bbox_height_px <= 0:
        return None
    real_height_m = TYPICAL_OBJECT_HEIGHTS_M.get(class_name, default_height_m)
    return (real_height_m * focal_length_px) / bbox_height_px


def pixel_to_3d(bbox: BoundingBox, depth_m: float, intrinsics: CameraIntrinsics) -> Point3D:
    """Back-project a bounding box center and depth into camera-relative 3D coordinates.

    Uses the standard pinhole model: X = (u - cx) * Z / f, Y = (v - cy) * Z / f, Z = depth.
    """
    u = (bbox.x_min + bbox.x_max) / 2.0
    v = (bbox.y_min + bbox.y_max) / 2.0
    x_m = (u - intrinsics.principal_point_x) * depth_m / intrinsics.focal_length_px
    y_m = (v - intrinsics.principal_point_y) * depth_m / intrinsics.focal_length_px
    return Point3D(x_m=x_m, y_m=y_m, z_m=depth_m)
