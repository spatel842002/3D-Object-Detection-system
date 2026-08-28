"""Lightweight IoU-based multi-object tracker for video inference.

This is intentionally a simple greedy IoU matcher (no motion model / Kalman
filter) so it has zero extra heavyweight dependencies. It is adequate for
short clips at typical frame rates; see docs/model-card.md for limitations
under fast motion or heavy occlusion.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .schemas import BoundingBox, DetectedObject


def iou(a: BoundingBox, b: BoundingBox) -> float:
    x_min = max(a.x_min, b.x_min)
    y_min = max(a.y_min, b.y_min)
    x_max = min(a.x_max, b.x_max)
    y_max = min(a.y_max, b.y_max)

    inter_w = max(0.0, x_max - x_min)
    inter_h = max(0.0, y_max - y_min)
    intersection = inter_w * inter_h

    area_a = max(0.0, a.x_max - a.x_min) * max(0.0, a.y_max - a.y_min)
    area_b = max(0.0, b.x_max - b.x_min) * max(0.0, b.y_max - b.y_min)
    union = area_a + area_b - intersection
    if union <= 0:
        return 0.0
    return intersection / union


@dataclass
class _Track:
    track_id: int
    class_name: str
    bbox: BoundingBox
    frames_since_seen: int = 0


@dataclass
class IouTracker:
    """Assigns stable track IDs to detections across sequential frames."""

    iou_threshold: float = 0.3
    max_frames_missing: int = 5
    _next_id: int = field(default=1, init=False)
    _tracks: list[_Track] = field(default_factory=list, init=False)

    def update(self, detections: list[DetectedObject]) -> list[DetectedObject]:
        """Match detections to existing tracks, mutating and returning them with track_id set."""
        unmatched_tracks = list(self._tracks)
        updated: list[DetectedObject] = []

        for detection in detections:
            best_track: _Track | None = None
            best_iou = 0.0
            for track in unmatched_tracks:
                if track.class_name != detection.class_name:
                    continue
                score = iou(track.bbox, detection.bbox)
                if score > best_iou and score >= self.iou_threshold:
                    best_iou = score
                    best_track = track

            if best_track is not None:
                best_track.bbox = detection.bbox
                best_track.frames_since_seen = 0
                detection.track_id = best_track.track_id
                unmatched_tracks.remove(best_track)
            else:
                new_track = _Track(
                    track_id=self._next_id, class_name=detection.class_name, bbox=detection.bbox
                )
                self._next_id += 1
                self._tracks.append(new_track)
                detection.track_id = new_track.track_id

            updated.append(detection)

        for track in unmatched_tracks:
            track.frames_since_seen += 1
        self._tracks = [t for t in self._tracks if t.frames_since_seen <= self.max_frames_missing]

        return updated
