"""
Signed URL Security Middleware
==============================
Validates signed URLs for object storage access with hardening policies.
"""

import logging
from typing import Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..services.storage_service import StorageService

logger = logging.getLogger("api.middleware.signed_url")

class SignedURLValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate signed URLs for secure object storage access.
    """

    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs", "/redoc", "/openapi.json", "/health", "/metrics"
        ]

    async def dispatch(self, request: Request, call_next):
        # Skip validation for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Check if this is a signed URL access attempt
        if self._is_signed_url_request(request):
            if not await self._validate_signed_url_access(request):
                logger.warning(f"Invalid signed URL access attempt: {request.url}")
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "Access denied",
                        "message": "Invalid or expired signed URL",
                        "code": "SIGNED_URL_INVALID"
                    }
                )

        return await call_next(request)

    def _is_signed_url_request(self, request: Request) -> bool:
        """Check if the request appears to be accessing a signed URL."""
        # Check for S3 signed URL parameters
        query_params = dict(request.query_params)
        signed_params = ['X-Amz-Algorithm', 'X-Amz-Credential', 'X-Amz-Signature']

        return any(param in query_params for param in signed_params)

    async def _validate_signed_url_access(self, request: Request) -> bool:
        """Validate the signed URL access."""
        try:
            # Get client IP
            client_ip = self._get_client_ip(request)

            # Get user agent
            user_agent = request.headers.get('User-Agent')

            # Validate the signed URL
            full_url = str(request.url)
            return await StorageService.validate_signed_url_access(
                url=full_url,
                client_ip=client_ip,
                user_agent=user_agent
            )

        except Exception as e:
            logger.error(f"Error validating signed URL: {e}")
            return False

    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Extract client IP address from request."""
        # Check X-Forwarded-For header (for proxies/load balancers)
        x_forwarded_for = request.headers.get('X-Forwarded-For')
        if x_forwarded_for:
            # Take the first IP in the chain
            return x_forwarded_for.split(',')[0].strip()

        # Check X-Real-IP header
        x_real_ip = request.headers.get('X-Real-IP')
        if x_real_ip:
            return x_real_ip.strip()

        # Fall back to direct connection
        return request.client.host if request.client else None