from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException, status
import logging
from jose import jwt, JWTError
from typing import Optional
from functools import wraps
from ..services.feature_flags import get_feature_service
from ..config import get_settings_instance

logger = logging.getLogger(__name__)

async def feature_flag_middleware(request: Request, call_next):
    """Middleware to inject checked flags for the current user into request.state.features."""
    feature_service = get_feature_service()
    
    # 1. Extract context (user_id, tenant_id) from JWT if present
    auth_header = request.headers.get("Authorization")
    user_id = None
    tenant_id = None
    
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            s = get_settings_instance()
            payload = jwt.decode(token, s.SECRET_KEY, algorithms=[s.jwt_algorithm])
            user_id = payload.get("sub")
            tenant_id = payload.get("tid")
        except (JWTError, Exception):
            pass # Invalid token doesn't crash the middleware, flags default to false

    # 2. Pre-cache relevant flags for this request lifecycle
    all_flags = feature_service.get_all_flags()
    request.state.features = {
        name: feature_service.is_enabled(name, user_id, tenant_id)
        for name in all_flags.keys()
    }
    
    return await call_next(request)

def feature_enabled(feature_name: str):
    """
    Decorator for FastAPI endpoints.
    Aborts with 404 NOT FOUND if the feature flag is disabled.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Try to get the request from either args or kwargs
            request: Optional[Request] = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if not request:
                 logger.error(f"Decorator feature_enabled('{feature_name}') requires 'request' object in endpoint signature.")
                 return await func(*args, **kwargs)

            features = getattr(request.state, "features", {})
            if not features.get(feature_name, False):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Feature '{feature_name}' is not available at this time."
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator
