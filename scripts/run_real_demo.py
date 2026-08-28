"""Run the real YOLOv8n + MiDaS_small pipeline on a real image and save evidence.

Downloads pretrained weights on first run (network required). Produces:
  - data/artifacts/demo/<name>_annotated.jpg  (bounding boxes + depth labels)
  - data/artifacts/demo/<name>_result.json    (full structured inference output)

Usage:
    python scripts/download_sample_assets.py   # one time, fetches a licensed sample photo
    python scripts/run_real_demo.py data/samples/street_scene_sample.jpg
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from threed_od.depth import MidasDepthEstimator  # noqa: E402
from threed_od.detection import YoloDetector  # noqa: E402
from threed_od.pipeline import DetectionPipeline, PipelineConfig  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "artifacts" / "demo"


def annotate(image_bgr, response) -> cv2.typing.MatLike:
    canvas = image_bgr.copy()
    for obj in response.objects:
        p1 = (int(obj.bbox.x_min), int(obj.bbox.y_min))
        p2 = (int(obj.bbox.x_max), int(obj.bbox.y_max))
        cv2.rectangle(canvas, p1, p2, (0, 220, 0), 2)
        depth_label = f"{obj.depth_m:.1f}m" if obj.depth_m is not None else "n/a"
        label = f"{obj.class_name} {obj.confidence:.2f} | {depth_label}"
        cv2.putText(
            canvas, label, (p1[0], max(0, p1[1] - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 220, 0), 1
        )
    return canvas


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <path-to-image>", file=sys.stderr)
        return 1

    image_path = Path(sys.argv[1])
    if not image_path.exists():
        print(f"ERROR: image not found: {image_path}", file=sys.stderr)
        return 1

    print("Loading YOLOv8n detector (downloads weights on first run)...")
    detector = YoloDetector(weights="yolov8n.pt", device="cpu", confidence_threshold=0.35)
    print("Loading MiDaS_small depth model (downloads weights on first run)...")
    depth_estimator = MidasDepthEstimator(model_name="MiDaS_small", device="cpu")

    config = PipelineConfig(
        focal_length_px=721.5,
        principal_point_x=None,
        principal_point_y=None,
        default_object_height_m=1.7,
    )
    pipeline = DetectionPipeline(detector, depth_estimator, config)

    image_bgr = cv2.imread(str(image_path))
    if image_bgr is None:
        print(f"ERROR: could not decode image: {image_path}", file=sys.stderr)
        return 1
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    print("Running inference...")
    response = pipeline.run_on_image(image_bgr, image_rgb)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = image_path.stem
    annotated_path = OUTPUT_DIR / f"{stem}_annotated.jpg"
    result_path = OUTPUT_DIR / f"{stem}_result.json"

    cv2.imwrite(str(annotated_path), annotate(image_bgr, response))
    result_path.write_text(response.model_dump_json(indent=2), encoding="utf-8")

    print(f"\nDetected {len(response.objects)} object(s) in {response.inference_latency_ms:.1f}ms")
    for obj in response.objects:
        print(f"  - {obj.class_name} (conf={obj.confidence:.2f}) depth~={obj.depth_m}")
    print(f"\nAnnotated image: {annotated_path}")
    print(f"Structured result: {result_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
