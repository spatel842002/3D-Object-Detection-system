"""ASGI entrypoint: `uvicorn threed_od.main:app`."""

from .api.app import app
from .config import get_settings
from .telemetry import configure_tracing

settings = get_settings()
configure_tracing(settings.otel_service_name, settings.otel_exporter_otlp_endpoint, app=app)

__all__ = ["app"]
