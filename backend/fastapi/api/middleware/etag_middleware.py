"""
ETag Middleware for FastAPI

Provides HTTP ETag header support for caching static resources.
- Computes MD5 hash of JSON response bodies
- Returns 304 Not Modified when content hasn't changed
- Skips ETag computation for streaming responses
- Reduces bandwidth for repeated requests to static endpoints
"""

import hashlib
import json
import logging
from typing import Callable, Optional, Set

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, StreamingResponse

logger = logging.getLogger("api.etag")


class ETagMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add ETag headers for HTTP caching optimization.
    
    Features:
    - Computes MD5 hash of response bodies for ETag generation
    - Compares against If-None-Match header from client
    - Returns 304 Not Modified with empty body when content unchanged
    - Skips ETag computation for streaming responses (to avoid blocking)
    - Adds ETag header to all applicable GET responses
    
    This significantly reduces bandwidth for static resources like:
    - Question geometries (/api/v1/questions)
    - System prompts
    - Language dictionaries
    """
    
    # Path patterns that should have ETag caching enabled
    # These are typically static resources that don't change frequently
    ETAG_ENABLED_PATHS: Set[str] = {
        "/api/v1/questions",
        "/api/v1/questions/categories",
    }
    
    # Path prefixes that should have ETag caching enabled
    ETAG_ENABLED_PREFIXES: Set[str] = {
        "/api/v1/questions/",
    }
    
    def __init__(self, app: Callable, enabled_paths: Optional[Set[str]] = None, 
                 enabled_prefixes: Optional[Set[str]] = None):
        """
        Initialize ETag middleware.
        
        Args:
            app: The ASGI application
            enabled_paths: Set of exact paths to enable ETag for (optional, extends defaults)
            enabled_prefixes: Set of path prefixes to enable ETag for (optional, extends defaults)
        """
        super().__init__(app)
        if enabled_paths:
            self.ETAG_ENABLED_PATHS = self.ETAG_ENABLED_PATHS | enabled_paths
        if enabled_prefixes:
            self.ETAG_ENABLED_PREFIXES = self.ETAG_ENABLED_PREFIXES | enabled_prefixes
    
    def _should_process_etag(self, request: Request) -> bool:
        """
        Check if ETag processing should be applied to this request.
        
        Only applies to GET requests for enabled paths.
        """
        # Only process GET requests
        if request.method != "GET":
            return False
        
        path = request.url.path
        
        # Check exact path match
        if path in self.ETAG_ENABLED_PATHS:
            return True
        
        # Check prefix match
        for prefix in self.ETAG_ENABLED_PREFIXES:
            if path.startswith(prefix):
                return True
        
        return False
    
    def _compute_etag(self, body: bytes) -> str:
        """
        Compute ETag (MD5 hash) for response body.
        
        Args:
            body: Raw response body bytes
            
        Returns:
            MD5 hash string wrapped in quotes per HTTP spec
        """
        hash_value = hashlib.md5(body).hexdigest()
        # ETags should be wrapped in quotes per HTTP spec
        return f'"{hash_value}"'
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with ETag support.
        
        1. Check if request should have ETag processing
        2. Execute request and get response
        3. If streaming response, return as-is (skip ETag)
        4. Capture response body and compute ETag hash
        5. Compare against If-None-Match header
        6. Return 304 if match, otherwise return response with ETag header
        """
        # Check if we should process ETag for this request
        should_process = self._should_process_etag(request)
        
        # Process the request
        response = await call_next(request)
        
        # Skip ETag processing if not applicable
        if not should_process:
            return response
        
        # Skip ETag for streaming responses (can't hash without consuming stream)
        if isinstance(response, StreamingResponse):
            logger.debug(f"Skipping ETag for streaming response: {request.url.path}")
            return response
        
        # Only process successful responses (200 OK)
        if response.status_code != 200:
            return response
        
        try:
            # Consume the body iterator and rebuild the response
            body_chunks = []
            async for chunk in response.body_iterator:
                if isinstance(chunk, str):
                    body_chunks.append(chunk.encode('utf-8'))
                else:
                    body_chunks.append(chunk)
            
            body = b''.join(body_chunks)
            
            if not body:
                return response
            
            # Compute ETag
            etag = self._compute_etag(body)
            
            # Check If-None-Match header from client
            if_none_match = request.headers.get("if-none-match")
            
            if if_none_match and if_none_match == etag:
                # Content hasn't changed - return 304 Not Modified
                logger.debug(f"ETag match for {request.url.path}, returning 304")
                return Response(
                    status_code=304,
                    headers={
                        "ETag": etag,
                        "Cache-Control": "private, must-revalidate"
                    }
                )
            
            # Content changed or no If-None-Match header
            # We need to reconstruct the response since we consumed the body_iterator
            new_response = Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
                background=response.background if hasattr(response, 'background') else None
            )
            new_response.headers["ETag"] = etag
            new_response.headers["Cache-Control"] = "private, must-revalidate"
            
            return new_response
            
        except Exception as e:
            # If ETag processing fails, log error and return original response
            logger.warning(f"ETag processing failed for {request.url.path}: {e}")
            return response


class ConditionalETagMiddleware(BaseHTTPMiddleware):
    """
    Alternative ETag middleware that operates on all JSON GET responses
    unless explicitly excluded. Use with caution on dynamic endpoints.
    
    This is useful when you want ETag support broadly but need to 
    explicitly mark dynamic endpoints that shouldn't be cached.
    """
    
    # Paths that should NEVER have ETag (dynamic/user-specific data)
    ETAG_EXCLUDED_PATHS: Set[str] = {
        "/api/v1/auth/me",
        "/api/v1/users/me",
    }
    
    # Path prefixes that should NEVER have ETag
    ETAG_EXCLUDED_PREFIXES: Set[str] = {
        "/api/v1/auth/",
        "/api/v1/analytics/",
        "/api/v1/journal/",
        "/api/v1/assessments/",
        "/api/v1/exams/",
        "/api/v1/profiles/medical",
    }
    
    def _should_exclude(self, request: Request) -> bool:
        """Check if this path should be excluded from ETag processing."""
        path = request.url.path
        
        # Check exact path exclusion
        if path in self.ETAG_EXCLUDED_PATHS:
            return True
        
        # Check prefix exclusion
        for prefix in self.ETAG_EXCLUDED_PREFIXES:
            if path.startswith(prefix):
                return True
        
        return False
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with conditional ETag support."""
        response = await call_next(request)
        
        # Only process successful GET requests
        if request.method != "GET":
            return response
        
        if response.status_code != 200:
            return response
        
        # Skip excluded paths
        if self._should_exclude(request):
            return response
        
        # Skip streaming responses
        if isinstance(response, StreamingResponse):
            return response
        
        try:
            # Consume the body iterator and rebuild the response
            body_chunks = []
            async for chunk in response.body_iterator:
                if isinstance(chunk, str):
                    body_chunks.append(chunk.encode('utf-8'))
                else:
                    body_chunks.append(chunk)
            
            body = b''.join(body_chunks)
            
            if not body:
                return response
            
            # Compute ETag
            etag = hashlib.md5(body).hexdigest()
            etag_header = f'"{etag}"'
            
            # Check If-None-Match
            if_none_match = request.headers.get("if-none-match")
            
            if if_none_match and if_none_match == etag_header:
                return Response(
                    status_code=304,
                    headers={
                        "ETag": etag_header,
                        "Cache-Control": "private, must-revalidate"
                    }
                )
            
            # Return response with ETag
            new_response = Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
                background=response.background if hasattr(response, 'background') else None
            )
            new_response.headers["ETag"] = etag_header
            new_response.headers["Cache-Control"] = "private, must-revalidate"
            
            return new_response
            
        except Exception as e:
            logger.warning(f"Conditional ETag processing failed: {e}")
            return response


def create_etag_middleware(enabled_paths: Optional[Set[str]] = None,
                           enabled_prefixes: Optional[Set[str]] = None) -> type:
    """
    Factory function to create ETag middleware with custom configuration.
    
    Usage:
        from api.middleware.etag_middleware import create_etag_middleware
        
        ETagMiddleware = create_etag_middleware(
            enabled_paths={"/api/v1/custom/resource"},
            enabled_prefixes={"/api/v1/static/"}
        )
        app.add_middleware(ETagMiddleware)
    
    Args:
        enabled_paths: Additional exact paths to enable ETag for
        enabled_prefixes: Additional path prefixes to enable ETag for
        
    Returns:
        Configured ETagMiddleware class
    """
    class ConfiguredETagMiddleware(ETagMiddleware):
        def __init__(self, app: Callable):
            super().__init__(app, enabled_paths, enabled_prefixes)
    
    return ConfiguredETagMiddleware


def generate_etag_for_data(data: dict) -> str:
    """
    Generate an ETag for a dictionary of data.
    
    Utility function to generate ETags manually in route handlers if needed.
    
    Args:
        data: Dictionary to generate ETag for
        
    Returns:
        ETag string (MD5 hash wrapped in quotes)
    """
    body = json.dumps(data, sort_keys=True, ensure_ascii=False).encode('utf-8')
    hash_value = hashlib.md5(body).hexdigest()
    return f'"{hash_value}"'
