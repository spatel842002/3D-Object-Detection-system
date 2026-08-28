from __future__ import annotations

from threed_od.schemas import BoundingBox, DetectedObject
from threed_od.tracking import IouTracker, iou


def _det(class_name: str, x_min: float, y_min: float, x_max: float, y_max: float) -> DetectedObject:
    return DetectedObject(
        class_name=class_name,
        confidence=0.9,
        bbox=BoundingBox(x_min=x_min, y_min=y_min, x_max=x_max, y_max=y_max),
    )


def test_iou_identical_boxes_is_one() -> None:
    box = BoundingBox(x_min=0, y_min=0, x_max=10, y_max=10)
    assert iou(box, box) == 1.0


def test_iou_disjoint_boxes_is_zero() -> None:
    a = BoundingBox(x_min=0, y_min=0, x_max=10, y_max=10)
    b = BoundingBox(x_min=100, y_min=100, x_max=110, y_max=110)
    assert iou(a, b) == 0.0


def test_tracker_assigns_new_id_on_first_sighting() -> None:
    tracker = IouTracker()
    result = tracker.update([_det("person", 0, 0, 50, 100)])
    assert result[0].track_id == 1


def test_tracker_keeps_same_id_for_overlapping_detection_next_frame() -> None:
    tracker = IouTracker()
    tracker.update([_det("person", 0, 0, 50, 100)])
    result = tracker.update([_det("person", 2, 2, 52, 102)])  # slightly moved, high IoU
    assert result[0].track_id == 1


def test_tracker_assigns_new_id_when_object_reappears_far_away() -> None:
    tracker = IouTracker()
    tracker.update([_det("person", 0, 0, 50, 100)])
    result = tracker.update([_det("person", 500, 500, 550, 600)])  # no overlap
    assert result[0].track_id == 2


def test_tracker_does_not_match_across_different_classes() -> None:
    tracker = IouTracker()
    tracker.update([_det("person", 0, 0, 50, 100)])
    result = tracker.update([_det("car", 0, 0, 50, 100)])  # identical bbox, different class
    assert result[0].track_id == 2


def test_tracker_drops_track_after_max_frames_missing() -> None:
    tracker = IouTracker(max_frames_missing=2)
    tracker.update([_det("person", 0, 0, 50, 100)])
    tracker.update([])  # missing frame 1
    tracker.update([])  # missing frame 2
    tracker.update([])  # missing frame 3 -> track evicted
    result = tracker.update([_det("person", 0, 0, 50, 100)])
    assert result[0].track_id == 2  # new id, not reused
