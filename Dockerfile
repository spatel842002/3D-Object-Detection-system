# CPU inference image. See docs/deployment.md for the GPU/EC2 deployment mode,
# which uses a CUDA base image and the standard (non "+cpu") torch wheels instead.
FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

# CPU-only torch wheels keep the image small; swap for the default PyPI
# wheels (or a CUDA base image) for GPU deployment -- see docs/deployment.md.
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.9.1 torchvision==0.24.1 \
    && pip install --no-cache-dir -e .

ENV YOLO_DEVICE=cpu \
    DEPTH_DEVICE=cpu \
    PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "threed_od.main:app", "--host", "0.0.0.0", "--port", "8000"]
