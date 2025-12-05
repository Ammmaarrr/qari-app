"""
Logging Configuration
Structured JSON logging for production
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        if hasattr(record, "processing_time"):
            log_data["processing_time"] = record.processing_time

        if hasattr(record, "error_count"):
            log_data["error_count"] = record.error_count

        return json.dumps(log_data)


def setup_logging(
    level: str = "INFO", log_file: str = None, json_format: bool = True
) -> None:
    """
    Configure application logging

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for logs
        json_format: Use JSON formatting (recommended for production)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Create handlers
    handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    handlers.append(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        handlers.append(file_handler)

    # Set formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    for handler in handlers:
        handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add new handlers
    for handler in handlers:
        root_logger.addHandler(handler)

    # Suppress noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


# Logging middleware for FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time
import uuid


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests with timing
    """

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Add request_id to request state
        request.state.request_id = request_id

        # Log incoming request
        logger = logging.getLogger("api.request")
        logger.info(
            f"Incoming request: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
            },
        )

        # Process request
        response = await call_next(request)

        # Calculate processing time
        processing_time = time.time() - start_time

        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "processing_time": round(processing_time, 3),
            },
        )

        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Processing-Time"] = str(round(processing_time, 3))

        return response
