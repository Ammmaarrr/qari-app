"""
Metrics Collection
Prometheus metrics for monitoring
"""

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from fastapi import Response
import time
from functools import wraps


# Define metrics
http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

audio_processing_duration_seconds = Histogram(
    "audio_processing_duration_seconds",
    "Audio processing duration in seconds",
    ["stage"],  # normalize, transcribe, analyze
)

transcription_requests_total = Counter(
    "transcription_requests_total", "Total transcription requests", ["model"]
)

tajweed_errors_detected_total = Counter(
    "tajweed_errors_detected_total", "Total tajweed errors detected", ["error_type"]
)

tajweed_error_confidence = Histogram(
    "tajweed_error_confidence", "Confidence scores for detected errors", ["error_type"]
)

overall_recitation_score = Histogram(
    "overall_recitation_score", "Overall recitation scores"
)

active_analysis_tasks = Gauge(
    "active_analysis_tasks", "Number of currently active analysis tasks"
)

quick_analyze_pass_rate = Counter(
    "quick_analyze_results_total",
    "Quick analyze pass/fail counts",
    ["result"],  # passed or failed
)

model_inference_duration_seconds = Histogram(
    "model_inference_duration_seconds", "ML model inference duration", ["model_type"]
)


# Decorator for timing functions
def track_duration(metric_name: str, stage: str = None):
    """
    Decorator to track function execution duration
    """

    def decorator(func):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if stage:
                    audio_processing_duration_seconds.labels(stage=stage).observe(
                        duration
                    )
                else:
                    model_inference_duration_seconds.labels(
                        model_type=metric_name
                    ).observe(duration)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if stage:
                    audio_processing_duration_seconds.labels(stage=stage).observe(
                        duration
                    )
                else:
                    model_inference_duration_seconds.labels(
                        model_type=metric_name
                    ).observe(duration)

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Metrics endpoint
async def metrics_endpoint():
    """
    Endpoint to expose Prometheus metrics
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Helper functions for recording metrics
def record_transcription(model: str):
    """Record a transcription request"""
    transcription_requests_total.labels(model=model).inc()


def record_tajweed_error(error_type: str, confidence: float):
    """Record a detected tajweed error"""
    tajweed_errors_detected_total.labels(error_type=error_type).inc()
    tajweed_error_confidence.labels(error_type=error_type).observe(confidence)


def record_recitation_score(score: float):
    """Record an overall recitation score"""
    overall_recitation_score.observe(score)


def record_quick_analyze_result(passed: bool):
    """Record quick analyze result"""
    result = "passed" if passed else "failed"
    quick_analyze_pass_rate.labels(result=result).inc()


# Middleware for automatic HTTP metrics
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically collect HTTP metrics
    """

    async def dispatch(self, request: Request, call_next):
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Record metrics
        duration = time.time() - start_time
        method = request.method
        endpoint = request.url.path
        status = response.status_code

        http_requests_total.labels(
            method=method, endpoint=endpoint, status=status
        ).inc()

        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(
            duration
        )

        return response
