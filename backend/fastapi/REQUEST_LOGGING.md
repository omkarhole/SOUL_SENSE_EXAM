# Request-Level Logging Middleware

## Overview

The request-level logging middleware provides structured, JSON-formatted logging with unique request correlation IDs for every API request. This enables comprehensive request tracing, debugging, and monitoring across distributed systems.

## Features

- **Request Correlation IDs**: Every request gets a unique UUID4 identifier
- **Structured JSON Logging**: Machine-parsable logs for log aggregators (ELK, Splunk, Datadog)
- **Context Propagation**: Request IDs propagate through the entire request lifecycle via contextvars
- **PII Protection**: Sensitive endpoints don't log request/response bodies
- **Performance Tracking**: Automatic measurement of request processing time
- **Slow Request Detection**: Warnings for requests taking >500ms
- **Client IP Extraction**: Handles X-Forwarded-For and X-Real-IP proxy headers
- **Query Parameter Sanitization**: Masks sensitive params (password, token, secret, etc.)
- **CORS Integration**: X-Request-ID exposed to frontend for error correlation

## Architecture

### Components

1. **RequestLoggingMiddleware**: FastAPI middleware that intercepts all requests
2. **request_id_ctx**: ContextVar for thread-safe request ID propagation
3. **get_request_id()**: Helper function to access current request ID anywhere
4. **ContextualLogger**: Logger wrapper that auto-includes request IDs

### Flow

```
1. Request arrives → Middleware generates UUID4
2. Request ID stored in contextvar (thread-safe)
3. Log "request_started" with metadata
4. Process request through application
5. Log "request_completed" with status/timing
6. Add X-Request-ID header to response
7. Return response to client
```

## Implementation

### Middleware Registration

The middleware is registered in `main.py` as the innermost middleware to capture the full request lifecycle:

```python
from .middleware.logging_middleware import RequestLoggingMiddleware

app.add_middleware(RequestLoggingMiddleware)
```

**Important**: This should be the last middleware added (first to execute) to ensure it wraps all other middleware.

### CORS Configuration

The X-Request-ID header is exposed via CORS to allow frontend access:

```python
app.add_middleware(
    CORSMiddleware,
    expose_headers=["X-API-Version", "X-Request-ID", "X-Process-Time"],
)
```

### Accessing Request ID in Code

```python
from api.middleware.logging_middleware import get_request_id, ContextualLogger

# In any route handler, service, or utility function
async def some_service_function():
    request_id = get_request_id()  # Returns current request's UUID
    logger.info(f"Processing request {request_id}")
    
    # Or use ContextualLogger for automatic request ID injection
    ctx_logger = ContextualLogger()
    ctx_logger.info("This log automatically includes request_id")
```

## Log Format

### Request Started Event

```json
{
  "timestamp": "2026-02-26 10:30:45,123",
  "level": "INFO",
  "logger": "api.requests",
  "message": {
    "event": "request_started",
    "request_id": "a3f7b2c1-4d9e-4f12-a6b3-7e8d9f1a2b3c",
    "method": "POST",
    "path": "/api/v1/profiles",
    "client_ip": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "query_params": {"page": "1", "limit": "20"}
  }
}
```

### Request Completed Event

```json
{
  "timestamp": "2026-02-26 10:30:45,234",
  "level": "INFO",
  "logger": "api.requests",
  "message": {
    "event": "request_completed",
    "request_id": "a3f7b2c1-4d9e-4f12-a6b3-7e8d9f1a2b3c",
    "method": "POST",
    "path": "/api/v1/profiles",
    "status_code": 201,
    "process_time_ms": 111.45
  }
}
```

### Slow Request Warning

```json
{
  "timestamp": "2026-02-26 10:31:00,789",
  "level": "WARNING",
  "logger": "api.requests",
  "message": {
    "event": "slow_request",
    "request_id": "b8e3c4d5-6f2a-4b8c-97d1-3e5f6a7b8c9d",
    "method": "GET",
    "path": "/api/v1/exams",
    "process_time_ms": 742.30,
    "threshold_ms": 500
  }
}
```

## PII Protection

### Sensitive Endpoints

The following endpoints do NOT log request/response bodies to prevent PII leakage:

- `/api/v1/auth/login`
- `/api/v1/auth/register`
- `/api/v1/auth/password-reset`
- `/api/v1/profiles/medical`
- `/api/v1/users/me`

### Query Parameter Sanitization

Sensitive query parameters are masked in logs:

```python
# Original: ?password=secret123&token=abc&page=1
# Logged:   ?password=***REDACTED***&token=***REDACTED***&page=1
```

Masked parameters: `password`, `token`, `secret`, `key`, `apikey`, `api_key`, `otp`

## Testing

### Manual Testing

1. Start the FastAPI server:
   ```bash
   cd backend/fastapi
   uvicorn api.main:app --reload
   ```

2. Make a test request:
   ```bash
   curl -v http://localhost:8000/api/v1/health
   ```

3. Verify response headers include `X-Request-ID`:
   ```
   X-Request-ID: a3f7b2c1-4d9e-4f12-a6b3-7e8d9f1a2b3c
   ```

4. Check server console for JSON-formatted logs

### Automated Testing

Run the comprehensive test suite:

```bash
cd backend/fastapi
python test_request_logging.py
```

Tests cover:
- Request ID generation and uniqueness
- Header propagation
- CORS exposure
- Concurrent request handling
- Error logging
- Sensitive endpoint protection

## Frontend Integration

### Reading Request ID

```javascript
// In your frontend API client
async function makeRequest(url) {
  const response = await fetch(url);
  const requestId = response.headers.get('X-Request-ID');
  
  if (!response.ok) {
    console.error(`Request ${requestId} failed with status ${response.status}`);
    // Include requestId in error reports
    Sentry.captureException(error, { tags: { request_id: requestId } });
  }
  
  return response.json();
}
```

### Error Correlation

When users report issues, ask for the Request ID from their browser's Network tab:

1. Open Developer Tools → Network tab
2. Click the failed request
3. Find `X-Request-ID` in response headers
4. Search backend logs for this ID to see full request lifecycle

## Log Aggregation

### ELK Stack Integration

```conf
# Logstash configuration
input {
  file {
    path => "/var/log/soul-sense/api.log"
    codec => "json"
  }
}

filter {
  json {
    source => "message"
  }
  
  # Extract request_id for correlation
  mutate {
    add_field => { "[@metadata][request_id]" => "%{[message][request_id]}" }
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "soul-sense-api-%{+YYYY.MM.dd}"
    document_id => "%{[@metadata][request_id]}_%{[@metadata][event]}"
  }
}
```

### Datadog Integration

```python
import logging
from ddtrace import tracer

# In main.py startup
import ddtrace
ddtrace.patch_all()

# Datadog automatically correlates logs with APM traces
# Request IDs provide additional correlation layer
```

### Splunk Integration

```conf
# inputs.conf
[monitor:///var/log/soul-sense/api.log]
sourcetype = _json
index = soul_sense

# props.conf
[_json]
KV_MODE = json
TIMESTAMP_FIELDS = timestamp
```

## Performance Considerations

### Overhead

- Request ID generation: ~0.01ms (UUID4)
- Context variable operations: ~0.001ms
- JSON serialization: ~0.1ms per log entry
- **Total overhead**: ~0.2-0.5ms per request (<1% for typical 50ms requests)

### Optimization Tips

1. **Adjust Slow Request Threshold**: Increase from 500ms if needed
   ```python
   SLOW_REQUEST_THRESHOLD_MS = 1000  # 1 second
   ```

2. **Disable Debug Logging in Production**: Set log level to INFO
   ```python
   logging.basicConfig(level=logging.INFO)
   ```

3. **Use Async Log Handlers**: For high-throughput systems
   ```python
   from concurrent.futures import ThreadPoolExecutor
   handler = QueueHandler(queue)  # Non-blocking log writes
   ```

## Troubleshooting

### Request ID Not Appearing in Logs

**Problem**: Logs don't include `request_id` field

**Solution**:
1. Verify middleware is registered in `main.py`
2. Check that `ContextualLogger` is being used
3. Ensure `get_request_id()` is called within request context

### Request ID Not in Response Headers

**Problem**: `X-Request-ID` header missing from responses

**Solution**:
1. Verify middleware is innermost (added last)
2. Check CORS `expose_headers` includes `X-Request-ID`
3. Ensure no other middleware is overwriting headers

### Sensitive Data in Logs

**Problem**: Passwords or tokens visible in logs

**Solution**:
1. Add endpoint to `SENSITIVE_PATHS` set:
   ```python
   SENSITIVE_PATHS = {
       "/api/v1/auth/login",
       "/api/v1/your/new/endpoint",  # Add here
   }
   ```

2. Add query param to sanitization list:
   ```python
   SENSITIVE_PARAMS = {"password", "token", "your_param"}
   ```

### High Memory Usage

**Problem**: Context variables causing memory leaks

**Solution**: Context variables auto-cleanup with request lifecycle. If issues persist:
1. Verify Python 3.7+ (contextvars introduced)
2. Check for long-lived background tasks holding context
3. Consider using separate context for background tasks:
   ```python
   from contextvars import copy_context
   ctx = copy_context()
   await asyncio.create_task(background_task(), context=ctx)
   ```

## Best Practices

1. **Always Include Request ID in Error Responses**:
   ```python
   from api.middleware.logging_middleware import get_request_id
   
   @router.get("/example")
   async def example():
       try:
           # ... your code
       except Exception as e:
           request_id = get_request_id()
           raise HTTPException(
               status_code=500,
               detail=f"Internal error. Request ID: {request_id}"
           )
   ```

2. **Use ContextualLogger for Service Logs**:
   ```python
   from api.middleware.logging_middleware import ContextualLogger
   
   logger = ContextualLogger()
   logger.info("User profile updated")  # Automatically includes request_id
   ```

3. **Correlate with Database Queries**:
   ```python
   # Add request ID to database query comments
   request_id = get_request_id()
   query = query.execution_options(
       query_comment=f"request_id:{request_id}"
   )
   ```

4. **Include in External API Calls**:
   ```python
   async def call_external_api():
       request_id = get_request_id()
       headers = {
           "X-Request-ID": request_id,  # Forward to downstream services
           "User-Agent": "SoulSense/1.0"
       }
       response = await http_client.get(url, headers=headers)
   ```

5. **Monitor Slow Request Patterns**:
   ```python
   # Set up alerting for frequent slow requests
   # Example Datadog monitor:
   # avg(last_5m):avg:soul_sense.request.duration{} > 500
   ```

## Security Considerations

1. **No PII in Logs**: Never log passwords, tokens, SSNs, credit cards
2. **Log Retention**: Rotate logs regularly (30-90 days max)
3. **Access Control**: Restrict log access to operators only
4. **Compliance**: Ensure logging meets GDPR/HIPAA requirements
5. **Encryption**: Encrypt logs at rest and in transit

## Changelog

### Version 1.0.0 (2024-02-26)

- Initial implementation with UUID4 request IDs
- JSON-structured logging
- Context variable propagation
- PII protection for sensitive endpoints
- CORS integration
- Query parameter sanitization
- Slow request detection (>500ms)
- Comprehensive test suite
- Documentation

## Related Issues

- Issue #936: Add Request-Level Logging Middleware (this implementation)
- Issue #934: Redis Rate Limiting (related infrastructure improvement)
- Issue #935: Switch Services to Async (future enhancement for async logging)

## References

- [FastAPI Middleware Documentation](https://fastapi.tiangolo.com/tutorial/middleware/)
- [Python contextvars Module](https://docs.python.org/3/library/contextvars.html)
- [Structured Logging Best Practices](https://www.structlog.org/)
- [Request ID Correlation Patterns](https://www.kennethreitz.org/essays/2016/02/25/a-better-pip-workflow)
