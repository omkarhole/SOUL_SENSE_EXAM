
import asyncio
import time
import os
import sys

# Set PYTHONPATH
test_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(test_dir, "backend", "fastapi")
sys.path.insert(0, project_root)

async def test_limiter_logic():
    from api.middleware.rate_limiter import TokenBucketLimiter
    
    # 1. Start Limiter
    limiter = TokenBucketLimiter("test_unit", default_capacity=5, default_refill_rate=1.0)
    
    print("\n[UT] Testing Token Bucket Burst (Capacity: 5)...")
    for i in range(7):
        allowed, remaining = await limiter.is_rate_limited("client_1")
        print(f"Request {i+1}: Allowed={allowed}, Remaining={remaining}")
    
    print("\n[UT] Waiting 2 seconds for refill...")
    await asyncio.sleep(2)
    
    allowed, remaining = await limiter.is_rate_limited("client_1")
    print(f"Request 8: Allowed={allowed}, Remaining={remaining} (Refilled?)")

if __name__ == "__main__":
    asyncio.run(test_limiter_logic())
