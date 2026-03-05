"""
FastAPI Middleware for File Descriptor Exhaustion Protection - Issue #1316

This middleware integrates Linux FD Guardrails with FastAPI to provide:
- Request rejection at critical FD usage levels (503 Service Unavailable)
- Backpressure through request delays at elevated usage
- Response headers with current FD status for monitoring
- Graceful degradation to prevent service crashes
"""

import time
import logging
from typing import Optional, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class FDExhaustionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to protect against file descriptor exhaustion.
    
    Features:
    - Rejects requests with 503 when FD usage is critical
    - Applies backpressure delays for degraded states
    - Adds FD status headers to responses
    - Tracks request outcomes for monitoring
    
    Usage:
        app.add_middleware(FDExhaustionMiddleware)
    """
    
    def __init__(
        self,
        app: ASGIApp,
        guardrails=None,
        reject_status_code: int = 503,
        reject_message: str = "Service temporarily unavailable due to high load",
        add_headers: bool = True,
        excluded_paths: Optional[list] = None
    ):
        """
        Initialize FD exhaustion middleware.
        
        Args:
            app: The ASGI application
            guardrails: LinuxFDGuardrails instance (uses global if None)
            reject_status_code: HTTP status code when rejecting requests
            reject_message: Message when rejecting requests
            add_headers: Whether to add FD status headers to responses
            excluded_paths: List of paths to exclude from FD checks
        """
        super().__init__(app)
        
        # Import here to avoid circular imports
        if guardrails is None:
            from ..utils.linux_fd_guardrails import get_fd_guardrails
            self.guardrails = get_fd_guardrails()
        else:
            self.guardrails = guardrails
        
        self.reject_status_code = reject_status_code
        self.reject_message = reject_message
        self.add_headers = add_headers
        self.excluded_paths = set(excluded_paths or [])
        self.excluded_paths.update({
            '/health', '/ready', '/startup',  # Health endpoints must always work
            '/metrics', '/healthz', '/livez', '/readyz'  # Common monitoring paths
        })
        
        logger.info("FDExhaustionMiddleware initialized")
    
    def _should_skip_check(self, request: Request) -> bool:
        """Check if request path should skip FD exhaustion check."""
        path = request.url.path
        return any(
            path == excluded or path.startswith(f"{excluded}/")
            for excluded in self.excluded_paths
        )
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with FD exhaustion protection."""
        # Skip check for excluded paths
        if self._should_skip_check(request):
            return await call_next(request)
        
        # Check if we can accept this request
        if not self.guardrails.can_accept_request():
            logger.warning(
                f"Rejecting request due to FD exhaustion: {request.method} {request.url.path}"
            )
            response = JSONResponse(
                status_code=self.reject_status_code,
                content={
                    "error": "Service Unavailable",
                    "message": self.reject_message,
                    "retry_after": 30
                },
                headers={"Retry-After": "30"}
            )
            return response
        
        # Apply backpressure delay if in degraded state
        delay = self.guardrails.get_backpressure_delay()
        if delay > 0:
            await self._apply_backpressure(delay, request)
        
        # Process the request
        start_time = time.time()
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            raise
        
        # Add FD status headers if enabled
        if self.add_headers:
            response = self._add_fd_headers(response)
        
        return response
    
    async def _apply_backpressure(self, delay: float, request: Request) -> None:
        """Apply backpressure delay."""
        logger.debug(
            f"Applying backpressure delay of {delay}s for {request.method} {request.url.path}"
        )
        time.sleep(delay)
    
    def _add_fd_headers(self, response: Response) -> Response:
        """Add FD status headers to response."""
        try:
            status = self.guardrails.get_status()
            response.headers["X-FD-Usage-Percent"] = str(status['usage_percent'])
            response.headers["X-FD-State"] = status['state']
            response.headers["X-FD-Current"] = str(status['current_fds'])
            response.headers["X-FD-Max"] = str(status['max_fds'])
        except Exception as e:
            logger.debug(f"Could not add FD headers: {e}")
        return response


class FDExhaustionMiddlewareConfig:
    """
    Configuration for FD exhaustion middleware.
    
    Allows fine-grained control over middleware behavior.
    """
    
    def __init__(
        self,
        enabled: bool = True,
        reject_at_critical: bool = True,
        apply_backpressure: bool = True,
        add_response_headers: bool = True,
        critical_retry_after: int = 30,
        excluded_paths: Optional[list] = None
    ):
        self.enabled = enabled
        self.reject_at_critical = reject_at_critical
        self.apply_backpressure = apply_backpressure
        self.add_response_headers = add_response_headers
        self.critical_retry_after = critical_retry_after
        self.excluded_paths = excluded_paths or []


def create_fd_exhaustion_middleware(
    config: Optional[FDExhaustionMiddlewareConfig] = None,
    guardrails=None
) -> FDExhaustionMiddleware:
    """
    Factory function to create FD exhaustion middleware with configuration.
    
    Usage:
        middleware = create_fd_exhaustion_middleware(
            FDExhaustionMiddlewareConfig(
                enabled=True,
                excluded_paths=['/webhook', '/callback']
            )
        )
        app.add_middleware(middleware)
    """
    config = config or FDExhaustionMiddlewareConfig()
    
    if not config.enabled:
        # Return a no-op middleware
        class NoOpMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next: Callable) -> Response:
                return await call_next(request)
        return NoOpMiddleware
    
    return lambda app: FDExhaustionMiddleware(
        app,
        guardrails=guardrails,
        reject_status_code=503,
        add_headers=config.add_response_headers,
        excluded_paths=config.excluded_paths
    )
