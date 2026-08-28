# Troubleshooting

## `pip install` fails on `torch`/`torchvision`

Install the CPU-only wheels explicitly before the editable install:

```bash
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.9.1 torchvision==0.24.1
pip install -e ".[dev]"
```

Without the `--index-url`, `pip` may resolve a much larger CUDA-bundled
wheel from PyPI even on a machine with no GPU.

## `torch.hub.load("intel-isl/MiDaS", ...)` fails with a network error

MiDaS weights and code are fetched from GitHub on first use and cached
under `~/.cache/torch/hub`. If you're behind a proxy or firewall, set the
standard `HTTP_PROXY`/`HTTPS_PROXY` environment variables, or pre-populate
the cache on a machine with access and copy `~/.cache/torch/hub` over.

## `413 Request Entity Too Large` on a small file

Check `MAX_UPLOAD_SIZE_MB` -- the check compares against the *decoded*
byte count, so a small image with an unusually large embedded thumbnail/
metadata blob could still trip it. Increase the limit via `.env` if
legitimate.

## `422 Unprocessable Entity` on a file that looks like a valid image

`cv2.imdecode` failed to decode it. Common causes: the file is actually
HEIC/AVIF (not in the currently supported formats -- convert to JPEG/PNG/
WebP), or the file is truncated/corrupted.

## `docker compose up` fails with "port is already allocated"

Another local project or service already has host port 8000 (API),
9000/9001 (MinIO), or 5001 (MLflow) bound -- common when running several
of this portfolio's projects side by side. Change the left-hand side of
the affected `ports:` mapping in `docker-compose.yml` (e.g. `"8080:8000"`)
or stop the conflicting container (`docker ps` to find it).

## `docker compose up` fails at the `minio` health check

Confirm no other process is bound to `9000`/`9001` locally
(`netstat -ano | findstr 9000` on Windows,
`lsof -i :9000` on macOS/Linux) and that Docker Desktop has enough memory
allocated (MinIO + MLflow + the API together need a modest but non-trivial
amount of RAM to start concurrently).

## Detections look correct but depth numbers seem far off

This is very likely expected, not a bug -- read
`docs/calibration-guide.md`. The two most common real causes:
1. `CAMERA_FOCAL_LENGTH_PX` doesn't match your actual camera/image source
   (the default is a KITTI-derived approximation, not calibrated to your
   input).
2. The detected object's real size differs from the assumed typical
   height in `TYPICAL_OBJECT_HEIGHTS_M` (e.g., a child, or a "car" that's
   actually a large SUV).

## `mypy` fails after adding a new module

Ensure new modules use `from __future__ import annotations` and full type
hints on public functions; `disallow_untyped_defs` is currently `false`
project-wide (see `pyproject.toml`) but new code should still be typed for
consistency with the rest of the codebase.

## CI's `docker-build` job times out waiting for `/health`

The container downloads model weights lazily on first *inference*
request, not at container start, so `/health` should return quickly
without any network dependency. If it's timing out, check
`docker logs threed-od-ci` in the CI output for a startup exception
(most likely a missing system library for OpenCV -- confirm
`libgl1`/`libglib2.0-0` are present in the image, per the `Dockerfile`).
