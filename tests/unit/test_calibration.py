from __future__ import annotations

import math

from threed_od.calibration import (
    CameraIntrinsics,
    estimate_metric_depth_m,
    pixel_to_3d,
)
from threed_od.schemas import BoundingBox


def test_estimate_metric_depth_known_class_uses_typical_height() -> None:
    # A "person" (typical height 1.70m) spanning 100px tall at f=700px:
    # depth = 1.70 * 700 / 100 = 11.9m
    bbox = BoundingBox(x_min=0, y_min=0, x_max=50, y_max=100)
    depth = estimate_metric_depth_m("person", bbox, focal_length_px=700, default_height_m=1.7)
    assert depth is not None
    assert math.isclose(depth, 11.9, rel_tol=1e-6)


def test_estimate_metric_depth_unknown_class_uses_default_height() -> None:
    bbox = BoundingBox(x_min=0, y_min=0, x_max=50, y_max=50)
    depth = estimate_metric_depth_m("unicorn", bbox, focal_length_px=500, default_height_m=2.0)
    assert depth is not None
    assert math.isclose(depth, 2.0 * 500 / 50, rel_tol=1e-6)


def test_estimate_metric_depth_degenerate_bbox_returns_none() -> None:
    bbox = BoundingBox(x_min=10, y_min=10, x_max=50, y_max=10)  # zero height
    assert (
        estimate_metric_depth_m("person", bbox, focal_length_px=700, default_height_m=1.7) is None
    )


def test_pixel_to_3d_center_of_image_has_zero_lateral_offset() -> None:
    intrinsics = CameraIntrinsics.from_image_size(
        image_width=200, image_height=200, focal_length_px=700
    )
    bbox = BoundingBox(x_min=90, y_min=90, x_max=110, y_max=110)  # centered on principal point
    point = pixel_to_3d(bbox, depth_m=10.0, intrinsics=intrinsics)
    assert math.isclose(point.x_m, 0.0, abs_tol=1e-6)
    assert math.isclose(point.y_m, 0.0, abs_tol=1e-6)
    assert math.isclose(point.z_m, 10.0)


def test_pixel_to_3d_off_center_produces_nonzero_lateral_offset() -> None:
    intrinsics = CameraIntrinsics.from_image_size(
        image_width=200, image_height=200, focal_length_px=700
    )
    bbox = BoundingBox(x_min=150, y_min=90, x_max=170, y_max=110)  # right of center
    point = pixel_to_3d(bbox, depth_m=10.0, intrinsics=intrinsics)
    assert point.x_m > 0

    bbox_left = BoundingBox(x_min=10, y_min=90, x_max=30, y_max=110)  # left of center
    point_left = pixel_to_3d(bbox_left, depth_m=10.0, intrinsics=intrinsics)
    assert point_left.x_m < 0


def test_intrinsics_default_principal_point_is_image_center() -> None:
    intrinsics = CameraIntrinsics.from_image_size(
        image_width=640, image_height=480, focal_length_px=700
    )
    assert intrinsics.principal_point_x == 320.0
    assert intrinsics.principal_point_y == 240.0


def test_intrinsics_explicit_principal_point_overrides_default() -> None:
    intrinsics = CameraIntrinsics.from_image_size(
        image_width=640,
        image_height=480,
        focal_length_px=700,
        principal_point_x=300.0,
        principal_point_y=250.0,
    )
    assert intrinsics.principal_point_x == 300.0
    assert intrinsics.principal_point_y == 250.0
