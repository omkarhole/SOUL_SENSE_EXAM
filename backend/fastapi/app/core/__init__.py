"""
Core module for standardized API error handling.

This module provides:
- Custom exception classes (exceptions.py)
- Global exception handlers (handlers.py)

Usage:
    from backend.fastapi.app.core.exceptions import (
        NotFoundError,
        ValidationError,
        AuthenticationError,
        # ... etc
    )
    
    # In your router
    @router.get("/users/{user_id}")
    async def get_user(user_id: int):
        user = await fetch_user(user_id)
        if not user:
            raise NotFoundError(resource="User", resource_id=str(user_id))
        return user
"""

from .exceptions import (
    # Base
    BaseAPIException,
    
    # 4xx Errors
    ValidationError,
    NotFoundError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    RateLimitError,
    BusinessLogicError,
    
    # 5xx Errors
    InternalServerError,
    ServiceUnavailableError,
    
    # Specialized
    UserNotFoundError,
    InvalidCredentialsError,
    TokenExpiredError,
    ResourceAlreadyExistsError,
    InvalidStateTransitionError,
)

from .handlers import register_exception_handlers

__all__ = [
    # Base
    "BaseAPIException",
    
    # 4xx Errors
    "ValidationError",
    "NotFoundError",
    "AuthenticationError",
    "AuthorizationError",
    "ConflictError",
    "RateLimitError",
    "BusinessLogicError",
    
    # 5xx Errors
    "InternalServerError",
    "ServiceUnavailableError",
    
    # Specialized
    "UserNotFoundError",
    "InvalidCredentialsError",
    "TokenExpiredError",
    "ResourceAlreadyExistsError",
    "InvalidStateTransitionError",
    
    # Handler registration
    "register_exception_handlers",
]
