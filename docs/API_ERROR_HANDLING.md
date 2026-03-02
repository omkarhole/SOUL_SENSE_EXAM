# API Error Handling Guide

## Quick Reference

All API errors return this standardized structure:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": [...],
    "request_id": "req-uuid"
  }
}
```

## Error Codes Reference

| Code | HTTP Status | Meaning |
|------|-------------|---------|
| VALIDATION_ERROR | 422 | Input validation failed |
| NOT_FOUND | 404 | Resource not found |
| AUTHENTICATION_ERROR | 401 | Not authenticated |
| AUTHORIZATION_ERROR | 403 | Permission denied |
| CONFLICT_ERROR | 409 | Resource conflict |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |
| INTERNAL_SERVER_ERROR | 500 | Server error |

## For Backend Developers

### Importing Exceptions

```python
from backend.fastapi.app.core import (
    ValidationError,
    NotFoundError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    RateLimitError,
    BusinessLogicError,
    InternalServerError,
)
```

### Common Usage Patterns

#### Resource Not Found
```python
user = user_service.get_user_by_id(user_id)
if not user:
    raise NotFoundError(resource="User", resource_id=str(user_id))
```

#### Validation Error
```python
if age < 10 or age > 120:
    raise ValidationError(
        message="Age must be between 10 and 120",
        details=[{"field": "age", "error": "Age out of valid range"}]
    )
```

#### Authentication Required
```python
if not token:
    raise AuthenticationError(message="Authentication required")
```

#### Permission Denied
```python
if not user.is_admin:
    raise AuthorizationError(message="Admin access required")
```

#### Rate Limiting
```python
if rate_limit_exceeded:
    raise RateLimitError(
        message="Too many requests",
        wait_seconds=60
    )
```

#### Business Logic Error
```python
if invalid_transition:
    raise BusinessLogicError(
        message="Cannot transition from PENDING to COMPLETED",
        code="INVALID_STATE_TRANSITION"
    )
```

## For Frontend Developers

### Error Response Handling

```typescript
interface APIError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: any[];
    request_id: string;
  };
}

// Axios interceptor example
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.data?.success === false) {
      const { code, message, details, request_id } = error.response.data.error;
      
      // Use error code for translations
      showErrorToast({
        title: getErrorTitle(code),
        message: message,
        requestId: request_id  // For support tickets
      });
    }
    return Promise.reject(error);
  }
);
```

### Error Code Translation Map

```typescript
const errorTranslations = {
  VALIDATION_ERROR: {
    title: 'Invalid Input',
    action: 'Please check your input and try again.'
  },
  NOT_FOUND: {
    title: 'Not Found',
    action: 'The requested resource does not exist.'
  },
  AUTHENTICATION_ERROR: {
    title: 'Session Expired',
    action: 'Please log in again.'
  },
  AUTHORIZATION_ERROR: {
    title: 'Access Denied',
    action: 'You do not have permission to access this resource.'
  },
  RATE_LIMIT_EXCEEDED: {
    title: 'Too Many Requests',
    action: 'Please wait a moment before trying again.'
  },
  INTERNAL_SERVER_ERROR: {
    title: 'Server Error',
    action: 'Something went wrong. Please try again later.'
  }
};
```

## Debugging with Request IDs

Every error response includes a `request_id`. When reporting issues:

1. Include the `request_id` in support tickets
2. Search server logs using the request ID
3. Correlate with distributed tracing if enabled

Example:
```
User reports: "I got an error"
Frontend shows: "Error: VALIDATION_ERROR (Request ID: req-abc-123)"
Support searches logs: grep "req-abc-123" /var/log/api.log
```

## Testing Error Responses

### Using curl

```bash
# Validation Error (422)
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{}'

# Not Found (404)
curl http://localhost:8000/api/v1/questions/categories/99999

# Authentication (401)
curl http://localhost:8000/api/v1/users/me
```

### Using the test script

```bash
python test_error_handling.py
```

## Migration from Old Format

### Before
```python
raise HTTPException(status_code=404, detail="User not found")
```

### After
```python
raise NotFoundError(resource="User", resource_id=user_id)
```

### Frontend Before
```typescript
const errorMessage = error.response.data.detail;
```

### Frontend After
```typescript
const { code, message, request_id } = error.response.data.error;
```

## Additional Resources

- [STANDARDIZED_ERROR_HANDLING.md](../STANDARDIZED_ERROR_HANDLING.md) - Full implementation details
- [PULL_REQUEST_STANDARDIZED_ERROR_RESPONSES.md](../PULL_REQUEST_STANDARDIZED_ERROR_RESPONSES.md) - PR documentation
