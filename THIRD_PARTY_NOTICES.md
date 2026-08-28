# Third-Party Notices

This project's original source code is MIT licensed (see LICENSE). It
depends on the following third-party software, models, and media at
runtime or build time. None of the binaries below are committed to this
repository; they are downloaded on demand per docs/deployment.md.

## Pretrained models

| Model | Source | License | Notes |
|---|---|---|---|
| YOLOv8n | [ultralytics/ultralytics](https://github.com/ultralytics/ultralytics) | **AGPL-3.0** | Pretrained COCO weights, downloaded at runtime by the `ultralytics` package. Used unmodified. **AGPL-3.0 compliance:** because this project exposes the model over a network (the FastAPI service), the AGPL's network-use clause applies to the `ultralytics` library. This repository's complete corresponding source is already public on GitHub at all times, which satisfies the source-availability requirement for the unmodified `ultralytics` dependency. If you fork this project and modify the `ultralytics` package itself (not just this repo's own code) and offer it as a network service, you must also publish your modified copy of `ultralytics` under AGPL-3.0. A commercial Ultralytics Enterprise License is available from Ultralytics if AGPL-3.0 obligations are not acceptable for your deployment. See [docs/licenses-and-attribution.md](docs/licenses-and-attribution.md). |
| MiDaS_small (depth estimation) | [intel-isl/MiDaS](https://github.com/isl-org/MiDaS) | MIT | Pretrained depth weights, downloaded at runtime via `torch.hub`. Used unmodified. |

## Key Python dependencies

| Package | License |
|---|---|
| fastapi | MIT |
| uvicorn | BSD-3-Clause |
| pydantic / pydantic-settings | MIT |
| numpy | BSD-3-Clause |
| opencv-python-headless | Apache-2.0 |
| torch / torchvision | BSD-3-Clause |
| ultralytics | AGPL-3.0 (see above) |
| timm | Apache-2.0 |
| boto3 | Apache-2.0 |
| mlflow | Apache-2.0 |
| prometheus-client | Apache-2.0 |
| opentelemetry-sdk / -exporter-otlp / -instrumentation-fastapi | Apache-2.0 |
| structlog | MIT / Apache-2.0 (dual) |

Exact pinned versions are in `pyproject.toml` and `requirements.txt`; each
package's authoritative license is in its own repository/PyPI page, which
takes precedence over this summary if there is ever a discrepancy.

## Sample media

| Asset | Source | License | Attribution |
|---|---|---|---|
| `data/samples/street_scene_sample.jpg` (downloaded on demand, not committed) | [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:%22Respect_the_Crosswalk%22_-_Flickr_-_Diego3336.jpg) | CC BY 2.0 | Photo "Respect the Crosswalk" by Diego Torres Silvestre (Flickr: Diego3336). Fetched by `scripts/download_sample_assets.py`; never committed to git. |

No other third-party photos, videos, or datasets are used or committed by
this repository.
