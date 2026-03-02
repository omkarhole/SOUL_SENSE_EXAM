
import asyncio
import os
import sys
import json
import uuid

# Set PYTHONPATH
test_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(test_dir, "backend", "fastapi")
sys.path.insert(0, project_root)

async def demo_maintenance_mode():
    from api.middleware.maintenance import MaintenanceMiddleware
    
    # Mock Cache Service
    class MockCache:
        def __init__(self): self.state = None
        async def get(self, key): return self.state
        async def set(self, key, val, ttl_seconds=0): self.state = val
        async def delete(self, key): self.state = None
    
    cache_service = MockCache()
    MAINTENANCE_KEY = "soulsense:maintenance_state"
    
    # Patch middleware to use mock cache
    import api.middleware.maintenance
    api.middleware.maintenance.cache_service = cache_service
    
    async def call_next(request):
        from fastapi import Response
        return Response(content=json.dumps({"status": "success", "user": "authorized"}), media_type="application/json")

    middleware = MaintenanceMiddleware(None)
    
    print(f"\n{'='*70}")
    print(f"MAINTENANCE MODE & READ-ONLY GRACE PERIOD DEMO (#1112)")
    print(f"{'='*70}")

    # 1. READ_ONLY Scenario
    print("\n[SCENARIO 1] MODE: READ_ONLY (Grace Period)")
    await cache_service.set(MAINTENANCE_KEY, {"mode": "READ_ONLY", "retry_after": 60, "reason": "DB Migration in progress."})
    
    class MockRequest:
        def __init__(self, method, path, headers=None):
            self.method = method
            self.url = type('Url', (), {'path': path})
            self.headers = headers or {}

    # GET request - Should Pass
    req_get = MockRequest("GET", "/api/v1/journal", {})
    res_get = await middleware.dispatch(req_get, call_next)
    print(f"  [GET] /api/v1/journal: {'ALLOWED' if not hasattr(res_get, 'status_code') or res_get.status_code == 200 else 'BLOCKED'}")

    # POST request - Should Block
    req_post = MockRequest("POST", "/api/v1/journal", {})
    res_post = await middleware.dispatch(req_post, call_next)
    if hasattr(res_post, 'status_code'):
        print(f"  [POST] /api/v1/journal: BLOCKED (Status: {res_post.status_code})")
        body = json.loads(res_post.body.decode())
        print(f"  [POST] Error: {body['error']}, Reason: {body['message']}")
    else:
        print(f"  [POST] /api/v1/journal: ALLOWED (FAIL)")

    # 2. FULL MAINTENANCE Scenario
    print("\n[SCENARIO 2] MODE: MAINTENANCE (Admin Only)")
    await cache_service.set(MAINTENANCE_KEY, {"mode": "MAINTENANCE", "retry_after": 300})
    
    # GET request - Should now Block
    res_get_maint = await middleware.dispatch(req_get, call_next)
    if hasattr(res_get_maint, 'status_code'):
        print(f"  [GET] /api/v1/journal: BLOCKED (Status: {res_get_maint.status_code})")
    else:
        print(f"  [GET] /api/v1/journal: ALLOWED (FAIL)")

    # Cleanup
    await cache_service.delete(MAINTENANCE_KEY)
    print("\n[CLEANUP] Maintenance Mode OFF. Ready for launch.")
    
    print("\nDemo finished.")

if __name__ == "__main__":
    asyncio.run(demo_maintenance_mode())
