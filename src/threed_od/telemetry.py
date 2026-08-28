"""Prometheus metrics and optional OpenTelemetry tracing setup."""

from __future__ import annotations

from fastapi import FastAPI
from prometheus_client import Counter, Histogram

INFERENCE_REQUESTS_TOTAL = Counter(
    "threed_od_inference_requests_total",
    "Total inference requests handled",
    ["endpoint", "outcome"],
)

INFERENCE_LATENCY_SECONDS = Histogram(
    "threed_od_inference_latency_seconds",
    "End-to-end inference latency in seconds",
    ["endpoint"],
)

DETECTED_OBJECTS_TOTAL = Counter(
    "threed_od_detected_objects_total",
    "Total number of objects detected",
    ["class_name"],
)


def configure_tracing(
    service_name: str, otlp_endpoint: str | None, app: FastAPI | None = None
) -> None:
    """Configure OTLP tracing and auto-instrument the FastAPI app, if an endpoint is set.

    No-op otherwise, so the service runs with zero external tracing
    dependency in local development.
    """
    if not otlp_endpoint:
        return

    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    provider = TracerProvider(resource=Resource.create({SERVICE_NAME: service_name}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint)))
    trace.set_tracer_provider(provider)

    if app is not None:
        FastAPIInstrumentor.instrument_app(app)
