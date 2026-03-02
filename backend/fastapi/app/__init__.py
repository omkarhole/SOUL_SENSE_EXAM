"""
FastAPI App Module

Provides standardized error handling for the SoulSense API.
"""

from .core import (
    BaseAPIException,
    ValidationError,
    NotFoundError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    RateLimitError,
    BusinessLogicError,
    InternalServerError,
    ServiceUnavailableError,
    UserNotFoundError,
    InvalidCredentialsError,
    TokenExpiredError,
    ResourceAlreadyExistsError,
    InvalidStateTransitionError,
    register_exception_handlers,
)

__all__ = [
    "BaseAPIException",
    "ValidationError",
    "NotFoundError",
    "AuthenticationError",
    "AuthorizationError",
    "ConflictError",
    "RateLimitError",
    "BusinessLogicError",
    "InternalServerError",
    "ServiceUnavailableError",
    "UserNotFoundError",
    "InvalidCredentialsError",
    "TokenExpiredError",
    "ResourceAlreadyExistsError",
    "InvalidStateTransitionError",
    "register_exception_handlers",
]
