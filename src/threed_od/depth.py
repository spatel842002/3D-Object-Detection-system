"""Monocular relative-depth estimation backed by a pretrained MiDaS model.

MiDaS outputs *relative, unitless* inverse depth -- it establishes which
pixels are nearer or farther within a single frame, but it does not by
itself produce metric (meter) distances. Metric distance in this project
comes from the similarity-triangle heuristic in calibration.py. See
docs/calibration-guide.md for the full explanation and error bounds.
"""

from __future__ import annotations

from typing import Protocol

import numpy as np

from .schemas import BoundingBox


class DepthEstimator(Protocol):
    def relative_depth_map(self, image_rgb: np.ndarray) -> np.ndarray: ...

    def relative_depth_at_bbox(self, depth_map: np.ndarray, bbox: BoundingBox) -> float: ...


class MidasDepthEstimator:
    """Wraps a pretrained MiDaS_small model loaded via torch.hub."""

    def __init__(self, model_name: str = "MiDaS_small", device: str = "cpu") -> None:
        import torch

        self._torch = torch
        self._device = torch.device(device)
        self._model = torch.hub.load("intel-isl/MiDaS", model_name, trust_repo=True)
        self._model.to(self._device)
        self._model.eval()

        transforms = torch.hub.load("intel-isl/MiDaS", "transforms", trust_repo=True)
        self._transform = (
            transforms.small_transform
            if model_name == "MiDaS_small"
            else transforms.default_transform
        )

    def relative_depth_map(self, image_rgb: np.ndarray) -> np.ndarray:
        input_tensor = self._transform(image_rgb).to(self._device)
        with self._torch.no_grad():
            prediction = self._model(input_tensor)
            prediction = self._torch.nn.functional.interpolate(
                prediction.unsqueeze(1),
                size=image_rgb.shape[:2],
                mode="bicubic",
                align_corners=False,
            ).squeeze()
        return prediction.cpu().numpy()

    def relative_depth_at_bbox(self, depth_map: np.ndarray, bbox: BoundingBox) -> float:
        h, w = depth_map.shape[:2]
        x_min = max(0, int(bbox.x_min))
        y_min = max(0, int(bbox.y_min))
        x_max = min(w, int(bbox.x_max))
        y_max = min(h, int(bbox.y_max))
        if x_max <= x_min or y_max <= y_min:
            return float(np.median(depth_map))
        region = depth_map[y_min:y_max, x_min:x_max]
        return float(np.median(region))
