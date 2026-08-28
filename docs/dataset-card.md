# Dataset Card

## No custom training dataset

This project performs no training and no fine-tuning. It runs pretrained,
unmodified weights (YOLOv8n trained on COCO; MiDaS_small trained on a mix
of depth datasets by its original authors). No dataset is bundled, stored,
or shipped with this repository.

## COCO (via YOLOv8n's pretraining)

- 80 object classes; full list in the
  [Ultralytics COCO dataset docs](https://docs.ultralytics.com/datasets/detect/coco/).
- This project did not download, use, or redistribute COCO images or
  annotations -- only the resulting pretrained weight file.

## Sample media used for manual QA and demo screenshots

| Asset | Source | License | Committed to repo? |
|---|---|---|---|
| `street_scene_sample.jpg` | Wikimedia Commons, "Respect the Crosswalk" by Diego Torres Silvestre | CC BY 2.0 | **No** -- fetched on demand by `scripts/download_sample_assets.py` into `data/samples/` (gitignored) |
| Synthetic test images (solid-color arrays with a drawn rectangle) | Generated in-process by `tests/conftest.py::make_test_image_bytes` | N/A (generated, not real-world) | No -- generated at test time, never written to disk |
| Synthetic test video (blank frames written via OpenCV) | Generated in-process by `tests/contract/test_api.py::_make_tiny_video_bytes` | N/A | No -- written to pytest's `tmp_path` |

No real personal photos, government IDs, or private data of any kind are
used anywhere in this project.

## Why no full COCO evaluation is reproduced here

Recomputing YOLOv8n's mAP against the full COCO val2017 set would require
downloading roughly 1GB of images/annotations, which this project
deliberately avoids requiring for its release gate (see
`docs/evaluation-methodology.md`). The upstream, independently published
mAP is cited instead in `docs/model-card.md`.
