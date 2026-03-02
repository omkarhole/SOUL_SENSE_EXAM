# Redis Rate Limiting Implementation - Issue #934

## Overview

This PR implements centralized Redis-backed rate limiting using `slowapi` to address DoS vulnerabilities and enable horizontal scaling with consistent rate limits across multiple worker nodes.

## Implementation Details

### 1. Redis Configuration

**Files Modified:**
- `.env.example` - Added Redis configuration variables
- `backend/fastapi/api/config.py` - Added Redis settings to BaseAppSettings

**Configuration Variables:**
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

The config now includes a `redis_url` property that constructs the full Redis connection URL.

### 2. Redis-Backed Rate Limiter

**Files Modified:**
- `backend/fastapi/api/utils/limiter.py` - Updated to use Redis storage

**Key Features:**
- **Redis Storage**: Uses `redis.asyncio` for async Redis connections
- **Proxy IP Handling**: Implements `get_real_ip()` function that properly extracts client IP from:
  - `X-Forwarded-For` header (first IP in chain)
  - `X-Real-IP` header (Nginx standard)
  - Direct `request.client.host` (fallback)
- **User-Based Rate Limiting**: Prioritizes authenticated user ID over IP address
- **Sliding Window Algorithm**: Slowapi provides token-bucket/sliding-window algorithms

**IP Extraction Logic:**
```python
def get_real_ip(request: Request) -> str:
    """Extract real client IP, handling proxy scenarios."""
    # 1. Check X-Forwarded-For (first IP = actual client)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # 2. Check X-Real-IP (Nginx)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 3. Fallback to direct connection
    return request.client.host
```

### 3. Application Lifecycle Integration

**Files Modified:**
- `backend/fastapi/api/main.py` - Added Redis initialization and cleanup

**Startup:**
- Connects to Redis and tests connectivity with `PING`
- Configures slowapi limiter with Redis storage URI
- Logs successful connection or falls back to in-memory storage

**Shutdown:**
- Gracefully closes Redis connection during application teardown

### 4. Rate Limiting Applied to Routes

**Tiered Rate Limits:**
- **Generic GET requests**: 100 requests/minute
  - Profile retrieval: `/api/v1/profiles/settings`
  - User info: `/api/v1/users/me`
  - Journal listing: `/api/v1/journal/`
  
- **Mutation Operations (POST/PATCH/DELETE)**: 10 requests/minute
  - Authentication: `/api/v1/auth/register`, `/api/v1/auth/login`
  - Profile creation: `/api/v1/profiles/settings`
  - Journal creation: `/api/v1/journal/`

- **Special Endpoints**:
  - CAPTCHA: 100 requests/minute
  - Username availability: 20 requests/minute

**Implementation Pattern:**
```python
@router.get("/profile")
@limiter.limit("100/minute")
async def get_profile(request: Request, current_user: User = Depends(get_current_user)):
    # Rate limiting applied before endpoint logic
    pass

@router.post("/profile")
@limiter.limit("10/minute")
async def create_profile(request: Request, data: ProfileCreate, ...):
    # Stricter limits for mutations
    pass
```

**Files Modified:**
- `backend/fastapi/api/routers/auth.py` - Added decorators to auth endpoints
- `backend/fastapi/api/routers/profiles.py` - Added decorators to profile endpoints
- `backend/fastapi/api/routers/journal.py` - Added decorators to journal endpoints
- `backend/fastapi/api/routers/users.py` - Added decorators to user endpoints

### 5. HTTP Response Headers

Slowapi automatically adds the following headers to responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1645567890
```

When rate limit is exceeded:
```
HTTP/1.1 429 Too Many Requests
Retry-After: 45
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1645567845
```

### 6. Dependencies

**Files Modified:**
- `backend/fastapi/requirements.txt` - Added `redis[asyncio]>=5.0.0`

**Existing Dependencies:**
- `slowapi>=0.1.9` (already present)
- `redis>=4.5.0` (root requirements.txt)

### 7. Docker Compose

**No Changes Required:**
- Redis container already exists in `docker-compose.yml`
- Environment variables already configured:
  ```yaml
  - REDIS_HOST=redis
  - REDIS_PORT=${REDIS_PORT}
  ```

## Acceptance Criteria Status

✅ **[DONE] Generic backend infrastructure successfully boots and connects to Redis**
- Redis connection initialized in lifespan startup
- Connectivity verified with `PING` command
- Graceful fallback to in-memory if Redis unavailable

✅ **[DONE] FastAPI injects X-RateLimit-* headers into responses**
- Slowapi automatically adds:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

✅ **[DONE] Exceeding threshold triggers HTTP 429**
- Slowapi returns 429 with appropriate error message
- `Retry-After` header included
- Custom exception handler in main.py: `_rate_limit_exceeded_handler`

## Edge Cases Handled

### Proxy Masking
**Problem:** Backend behind ALB/Docker ingress resolves all IPs to internal bridge IP (e.g., 172.x.x.x)

**Solution:** 
- `get_real_ip()` function extracts true client IP from proxy headers
- Priority: `X-Forwarded-For` > `X-Real-IP` > direct connection
- First IP in `X-Forwarded-For` chain used (actual client, not proxies)

### Multiple Workers
**Problem:** In-memory rate limiting fails with multiple uvicorn/gunicorn workers

**Solution:**
- Redis provides centralized storage
- All workers share same rate limit counters
- Consistent limits across horizontal scaling

### Authenticated vs Anonymous
**Problem:** Rate limiting authenticated users same as anonymous attackers

**Solution:**
- `get_user_id()` prioritizes authenticated user ID from JWT
- Format: `user:{username}` for authenticated, IP for anonymous
- Prevents one malicious user from blocking all users on same IP

## Testing

### Manual Testing with `hey` or Apache Bench

```bash
# Test generic GET endpoint (100/minute limit)
hey -n 250 -c 50 http://localhost:8000/api/v1/auth/captcha

# Expected: ~100 return 200, ~150 return 429

# Test mutation endpoint (10/minute limit)
hey -n 20 -c 5 -m POST \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test123"}' \
    http://localhost:8000/api/v1/auth/login

# Expected: ~10 return 200/400, ~10 return 429
```

### Automated Testing

```bash
cd backend/fastapi
python test_rate_limiting.py
```

The script tests:
1. High-limit endpoint (CAPTCHA - 100/min)
2. Low-limit endpoint (Register - 10/min)
3. Header presence and values
4. 429 response on limit exceeded

### Verify Redis Storage

```bash
# Connect to Redis
redis-cli

# Check rate limit keys
KEYS *

# Example output:
# 1) "slowapi:127.0.0.1:/api/v1/auth/captcha"
# 2) "slowapi:user:john_doe:/api/v1/journal/"

# Check TTL (time to live)
TTL "slowapi:127.0.0.1:/api/v1/auth/captcha"

# Check value (request count)
GET "slowapi:127.0.0.1:/api/v1/auth/captcha"
```

## Deployment Checklist

- [ ] Update `.env` with production Redis credentials
- [ ] Ensure Redis host is accessible from all worker nodes
- [ ] Configure Redis authentication if exposed externally
- [ ] Set up Redis persistence (RDB/AOF) for production
- [ ] Monitor Redis memory usage and set `maxmemory` policy
- [ ] Verify `X-Forwarded-For` header is properly set by ALB/Nginx
- [ ] Test rate limiting with production traffic patterns
- [ ] Set up alerts for high 429 error rates

## Monitoring

### Key Metrics to Track

1. **Rate Limit Hits:**
   - Monitor 429 error rate
   - Track which endpoints are rate-limited most
   - Alert on unusual spikes

2. **Redis Health:**
   - Connection errors
   - Memory usage
   - Key expiration rate
   - Latency

3. **False Positives:**
   - Legitimate users hitting limits
   - May need to adjust thresholds

### Logging

Rate limiting events are logged with:
- Client IP (real IP extraction)
- User ID (if authenticated)
- Endpoint path
- Rate limit status

Example:
```
[INFO] Rate limiting applied: user:john_doe accessed /api/v1/journal/ (remaining: 95/100)
[WARNING] Rate limit exceeded: 1.2.3.4 blocked from /api/v1/auth/login (retry after: 45s)
```

## Troubleshooting

### Redis Connection Fails
**Symptom:** Application starts but logs "Redis not available"

**Solution:**
1. Check Redis is running: `docker ps | grep redis`
2. Verify `REDIS_HOST` and `REDIS_PORT` in `.env`
3. Test connectivity: `redis-cli -h localhost -p 6379 ping`
4. Check firewall rules if Redis is remote

**Fallback:** Application will use in-memory rate limiting (not recommended for production)

### All Requests Return 429
**Symptom:** Rate limits trigger immediately even with low traffic

**Possible Causes:**
1. **Proxy IP not extracted:** All requests have same IP (Docker bridge)
   - Solution: Verify `X-Forwarded-For` header is set by proxy
   - Check logs for IP addresses (should see real IPs, not 172.x.x.x)

2. **Rate limit too strict:**
   - Solution: Adjust limits in decorators (`@limiter.limit("200/minute")`)

3. **Redis keys not expiring:**
   - Solution: Check Redis TTL configuration
   - Verify slowapi is using correct time window

### Rate Limiting Not Working
**Symptom:** Can exceed limits without getting 429

**Possible Causes:**
1. **Multiple workers without Redis:**
   - Check if Redis is actually connected (look for startup log)
   - Each worker maintains separate in-memory limits

2. **Rate limit decorator missing:**
   - Verify `@limiter.limit()` is above route decorator
   - Check `request: Request` parameter is present

3. **Custom key function issue:**
   - Review `get_user_id()` logic
   - Check if user IDs are being extracted correctly

## Future Enhancements

1. **Dynamic Rate Limits:**
   - Adjust limits based on user tier (free vs premium)
   - Time-of-day based limits

2. **Distributed Rate Limiting:**
   - Consider Redis Cluster for high availability
   - Implement circuit breakers

3. **Rate Limit Dashboard:**
   - Real-time monitoring UI
   - Historical rate limit analytics

4. **Whitelisting:**
   - Bypass rate limits for trusted IPs
   - Internal service-to-service calls

5. **Advanced Algorithms:**
   - Leaky bucket
   - Fixed window with burst allowance
   - Adaptive rate limiting based on system load

## References

- [SlowAPI Documentation](https://slowapi.readthedocs.io/)
- [Redis Rate Limiting Patterns](https://redis.io/docs/manual/patterns/rate-limiter/)
- [OWASP Rate Limiting](https://cheatsheetseries.owasp.org/cheatsheets/Denial_of_Service_Cheat_Sheet.html#rate-limiting)

## Author

Implementation completed for Issue #934 - Redis Rate Limiting
