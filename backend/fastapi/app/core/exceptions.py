"""
Standardized API Exception Classes

This module provides custom exception classes that enforce a consistent
JSON error response structure across all API endpoints.

Error Response Schema:
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "Human readable message",
        "details": [...],  // Optional additional details
        "request_id": "req-uuid"  // Added by exception handlers
    }
}
"""

from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status


class BaseAPIException(HTTPException):
    """
    Base exception class for all API errors.
    
    All custom exceptions should inherit from this class to ensure
    consistent error response formatting.
    """
    
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[List[Dict[str, Any]]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.code = code
        self.message = message
        self.details = details or []
        
        # Build the detail dict for parent HTTPException
        detail = {
            "success": False,
            "error": {
                "code": code,
                "message": message,
            }
        }
        
        if details:
            detail["error"]["details"] = details
            
        super().__init__(status_code=status_code, detail=detail, headers=headers)


# =============================================================================
# 4xx Client Error Exceptions
# =============================================================================

class ValidationError(BaseAPIException):
    """Raised when request validation fails (422)."""
    
    def __init__(
        self,
        message: str = "The provided input structure was invalid.",
        details: Optional[List[Dict[str, Any]]] = None
    ):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class NotFoundError(BaseAPIException):
    """Raised when a requested resource is not found (404)."""
    
    def __init__(
        self,
        resource: str = "Resource",
        resource_id: Optional[str] = None,
        details: Optional[List[Dict[str, Any]]] = None
    ):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with id '{resource_id}' not found"
            
        super().__init__(
            code="NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class AuthenticationError(BaseAPIException):
    """Raised when authentication fails (401)."""
    
    def __init__(
        self,
        message: str = "Authentication required",
        code: str = "AUTHENTICATION_ERROR",
        details: Optional[List[Dict[str, Any]]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        if headers is None:
            headers = {"WWW-Authenticate": "Bearer"}
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
            headers=headers
        )


class AuthorizationError(BaseAPIException):
    """Raised when user lacks permission (403)."""
    
    def __init__(
        self,
        message: str = "Access denied",
        code: str = "AUTHORIZATION_ERROR",
        details: Optional[List[Dict[str, Any]]] = None
    ):
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class ConflictError(BaseAPIException):
    """Raised when there's a resource conflict (409)."""
    
    def __init__(
        self,
        message: str = "Resource conflict",
        code: str = "CONFLICT_ERROR",
        details: Optional[List[Dict[str, Any]]] = None
    ):
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


class RateLimitError(BaseAPIException):
    """Raised when rate limit is exceeded (429)."""
    
    def __init__(
        self,
        message: str = "Too many requests",
        wait_seconds: int = 60,
        details: Optional[List[Dict[str, Any]]] = None
    ):
        all_details = details or []
        all_details.append({"wait_seconds": wait_seconds})
        
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=all_details
        )


class BusinessLogicError(BaseAPIException):
    """
    Raised when a business logic rule is violated.
    This is for domain-specific errors that don't fit other categories.
    """
    
    def __init__(
        self,
        message: str,
        code: str = "BUSINESS_LOGIC_ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[List[Dict[str, Any]]] = None
    ):
        super().__init__(
            code=code,
            message=message,
            status_code=status_code,
            details=details
        )


# =============================================================================
# 5xx Server Error Exceptions
# =============================================================================

class InternalServerError(BaseAPIException):
    """Raised when an unexpected server error occurs (500)."""
    
    def __init__(
        self,
        message: str = "An unexpected error occurred",
        details: Optional[List[Dict[str, Any]]] = None
    ):
        super().__init__(
            code="INTERNAL_SERVER_ERROR",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class ServiceUnavailableError(BaseAPIException):
    """Raised when a service is temporarily unavailable (503)."""
    
    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        details: Optional[List[Dict[str, Any]]] = None
    ):
        super().__init__(
            code="SERVICE_UNAVAILABLE",
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )


# =============================================================================
# Specialized Domain Exceptions
# =============================================================================

class UserNotFoundError(NotFoundError):
    """Raised when a user is not found."""
    
    def __init__(self, user_id: Optional[str] = None):
        super().__init__(resource="User", resource_id=user_id)


class InvalidCredentialsError(AuthenticationError):
    """Raised when login credentials are invalid."""
    
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(
            message=message,
            code="INVALID_CREDENTIALS"
        )


class TokenExpiredError(AuthenticationError):
    """Raised when an authentication token has expired."""
    
    def __init__(self, message: str = "Token has expired"):
        super().__init__(
            message=message,
            code="TOKEN_EXPIRED"
        )


class ResourceAlreadyExistsError(ConflictError):
    """Raised when trying to create a resource that already exists."""
    
    def __init__(self, resource: str = "Resource", field: Optional[str] = None):
        message = f"{resource} already exists"
        if field:
            message = f"{resource} with this {field} already exists"
        super().__init__(
            message=message,
            code="RESOURCE_ALREADY_EXISTS"
        )


class InvalidStateTransitionError(BusinessLogicError):
    """Raised when an invalid state transition is attempted."""
    
    def __init__(
        self,
        message: str = "Invalid state transition",
        from_state: Optional[str] = None,
        to_state: Optional[str] = None
    ):
        details = []
        if from_state and to_state:
            details.append({"from_state": from_state, "to_state": to_state})
        super().__init__(
            message=message,
            code="INVALID_STATE_TRANSITION",
            details=details
        )
