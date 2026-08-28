# Reproducible Sample Output / Demo Guide

This documents exactly how the screenshot in `docs/assets/screenshots/` and
the benchmark in `docs/benchmarks/latency_results.json` were produced, so
anyone can regenerate them from a clean clone.

## 1. Install and set up

```bash
python -m venv .venv
.venv/Scripts/activate           # macOS/Linux: source .venv/bin/activate
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.9.1 torchvision==0.24.1
pip install -e ".[dev]"
```

## 2. Fetch the licensed sample photo

```bash
python scripts/download_sample_assets.py
```

Downloads one CC BY 2.0 licensed street photo from Wikimedia Commons into
`data/samples/` (gitignored -- never committed). Attribution is written
alongside it and is also recorded in `THIRD_PARTY_NOTICES.md`.

## 3. Run real inference and produce evidence

```bash
python scripts/run_real_demo.py data/samples/street_scene_sample.jpg
```

On first run this downloads the real YOLOv8n (~6MB) and MiDaS_small
(~82MB) pretrained weights. It writes:

- `data/artifacts/demo/street_scene_sample_annotated.jpg` -- the input
  photo with real detection boxes, class labels, confidences, and
  estimated depth drawn on it.
- `data/artifacts/demo/street_scene_sample_result.json` -- the full
  structured API-shaped response for that image.

The committed copies used in documentation
(`docs/assets/screenshots/image_inference_demo.jpg` and the accompanying
`_result.json`) were produced by this exact command against this exact
photo on 2026-08-27; rerunning it will reproduce equivalent (not
necessarily byte-identical, since model download mirrors can vary)
detections.

## 4. Run the latency benchmark

```bash
python scripts/evaluate_latency.py --runs 20 --resolution 640x480
```

Writes `docs/benchmarks/latency_results.json` and logs the same
params/metrics to the local MLflow tracking server. View the MLflow UI
with:

```bash
mlflow ui --backend-store-uri file:./mlruns
```

## 5. Run the live API and try it yourself

```bash
uvicorn threed_od.main:app --reload
# in another terminal:
curl -F "file=@data/samples/street_scene_sample.jpg;type=image/jpeg" \
  http://localhost:8000/v1/infer/image | python -m json.tool
```

## Video demo

Supply any short (<= `MAX_VIDEO_DURATION_S`, default 30s) `.mp4` clip you
have rights to:

```bash
curl -F "file=@your_clip.mp4;type=video/mp4" http://localhost:8000/v1/infer/video
# -> {"job_id": "...", "status": "queued"}
curl http://localhost:8000/v1/jobs/<job_id>
```

No video clip is bundled with this repository (avoids any licensing
ambiguity); supply your own to exercise this path, or run
`tests/contract/test_api.py::test_infer_video_end_to_end_completes_with_frame_results`,
which synthesizes a tiny test video with OpenCV and exercises the same
code path automatically.
