"""
Global Exception Handlers for FastAPI

This module provides centralized exception handling to ensure all errors
are returned in the standardized format:

{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "Human readable message",
        "details": [...],
        "request_id": "req-uuid"
    }
}
"""

import logging
import traceback
import uuid
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .exceptions import BaseAPIException


# Configure logger
logger = logging.getLogger("api.exceptions")


def get_request_id(request: Request) -> str:
    """
    Extract or generate a request ID for error tracking.
    
    Checks for X-Request-ID header first, then falls back to
    request.state.request_id (set by logging middleware), 
    then generates a new UUID if neither exists.
    """
    # Try header first
    request_id = request.headers.get("X-Request-ID")
    if request_id:
        return request_id
    
    # Try request state (set by logging middleware)
    if hasattr(request.state, "request_id"):
        return request.state.request_id
    
    # Generate new ID
    return f"req-{uuid.uuid4().hex[:12]}"


def build_error_response(
    code: str,
    message: str,
    status_code: int,
    request_id: str,
    details: Any = None
) -> Dict[str, Any]:
    """
    Build the standardized error response structure.
    
    Args:
        code: Machine-readable error code
        message: Human-readable error message
        status_code: HTTP status code
        request_id: Unique identifier for request tracking
        details: Optional additional error details
    
    Returns:
        Standardized error response dictionary
    """
    error_response = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id
        }
    }
    
    if details:
        error_response["error"]["details"] = details
        
    return error_response


async def request_validation_error_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle FastAPI/Pydantic validation errors (422).
    
    Transforms Pydantic validation errors into the standardized format.
    """
    request_id = get_request_id(request)
    
    # Transform Pydantic errors into a cleaner format
    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get("loc", []))
        error_type = error.get("type", "")
        msg = error.get("msg", "")
        
        # Format: "field: message" or just the message for general errors
        if field:
            details.append(f"{field}: {msg}")
        else:
            details.append(msg)
    
    logger.warning(
        f"Validation error: {exc.errors()}",
        extra={"request_id": request_id, "path": request.url.path}
    )
    
    content = build_error_response(
        code="VALIDATION_ERROR",
        message="The provided input structure was invalid.",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        request_id=request_id,
        details=details
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=content
    )


async def starlette_http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handle Starlette HTTP exceptions (including FastAPI's HTTPException).
    
    Transforms raw HTTPExceptions into the standardized format.
    """
    request_id = get_request_id(request)
    
    # Get status code
    status_code = exc.status_code
    
    # Map common status codes to error codes
    status_code_map = {
        400: "BAD_REQUEST",
        401: "AUTHENTICATION_ERROR",
        403: "AUTHORIZATION_ERROR",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        408: "REQUEST_TIMEOUT",
        409: "CONFLICT",
        410: "GONE",
        413: "PAYLOAD_TOO_LARGE",
        415: "UNSUPPORTED_MEDIA_TYPE",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT",
    }
    
    code = status_code_map.get(status_code, f"HTTP_{status_code}")
    
    # Extract message from detail
    if isinstance(exc.detail, str):
        message = exc.detail
    elif isinstance(exc.detail, dict):
        # If it's already our format, return it with request_id added
        if "success" in exc.detail and "error" in exc.detail:
            exc.detail["error"]["request_id"] = request_id
            return JSONResponse(status_code=status_code, content=exc.detail)
        message = exc.detail.get("message", str(exc.detail))
    else:
        message = str(exc.detail)
    
    logger.warning(
        f"HTTP Exception {status_code}: {message}",
        extra={"request_id": request_id, "path": request.url.path}
    )
    
    content = build_error_response(
        code=code,
        message=message,
        status_code=status_code,
        request_id=request_id
    )
    
    headers = getattr(exc, "headers", None)
    return JSONResponse(
        status_code=status_code,
        content=content,
        headers=headers
    )


async def base_api_exception_handler(
    request: Request,
    exc: BaseAPIException
) -> JSONResponse:
    """
    Handle our custom BaseAPIException and its subclasses.
    
    These exceptions already have the correct structure, we just need to
    add the request_id.
    """
    request_id = get_request_id(request)
    
    # Get the detail dict from parent HTTPException
    content = exc.detail
    
    # Add request_id if not present
    if isinstance(content, dict) and "error" in content:
        content["error"]["request_id"] = request_id
    
    logger.info(
        f"API Exception: {exc.code} - {exc.message}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "error_code": exc.code
        }
    )
    
    headers = getattr(exc, "headers", None)
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=headers
    )


async def global_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Catch-all handler for unhandled exceptions.
    
    Logs the full traceback and returns a safe error response.
    """
    request_id = get_request_id(request)
    
    # Log the full error with traceback for debugging
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # In debug mode, include error details
    from ..config import get_settings_instance
    settings = get_settings_instance()
    
    if settings.debug:
        details = [{
            "type": type(exc).__name__,
            "traceback": traceback.format_exc().split("\n")[-5:]  # Last 5 lines
        }]
        message = f"Internal Server Error: {str(exc)}"
    else:
        details = None
        message = "An unexpected error occurred"
    
    content = build_error_response(
        code="INTERNAL_SERVER_ERROR",
        message=message,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=request_id,
        details=details
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=content
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers with the FastAPI application.
    
    This function should be called during app initialization to set up
    the global exception handling.
    
    Args:
        app: The FastAPI application instance
    """
    # Handle Pydantic validation errors
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    
    # Handle our custom exceptions (must be before StarletteHTTPException)
    app.add_exception_handler(BaseAPIException, base_api_exception_handler)
    
    # Handle standard HTTP exceptions
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
    
    # Catch-all for unhandled exceptions
    app.add_exception_handler(Exception, global_exception_handler)
    
    logger.info("Exception handlers registered successfully")
