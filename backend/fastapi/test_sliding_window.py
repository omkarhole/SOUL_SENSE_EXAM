import asyncio
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from api.middleware.rate_limiter_sliding import rate_limiter
from api.config import get_settings_instance

# Mocking the redis class directly for the test
class MockRedis:
    def __init__(self):
        self._store = {}
        
    def register_script(self, script):
        async def mock_execute(keys, args):
            key = keys[0]
            now = float(args[0])
            window = float(args[1])
            limit = int(args[2])
            
            if key not in self._store:
                self._store[key] = []
                
            # ZREMRANGEBYSCORE equivalent
            clear_before = now - window
            self._store[key] = [t for t in self._store[key] if t > clear_before]
            
            # ZCARD equivalent
            count = len(self._store[key])
            allowed = count < limit
            
            if allowed:
                self._store[key].append(now)
                
            return [1 if allowed else 0, limit - count - (1 if allowed else 0)]
            
        return mock_execute

async def run_test():
    logger.info("Setting up Mock Redis for Sliding Window Log test...")
    rate_limiter.redis = MockRedis()
    rate_limiter._script = rate_limiter.redis.register_script("mock_lua")
    
    ident = "testing_ip_127.0.0.1"
    limit = 5   # Allow 5 requests...
    window = 10 # ...per 10 seconds
    
    logger.info(f"Testing sliding window limiter. Limit: {limit} requests per {window} seconds.")
    
    # Send 5 requests quickly, which should succeed
    for i in range(1, 6):
        allowed, rem = await rate_limiter.check_rate_limit(ident, limit, window)
        logger.info(f"[Request {i}] Allowed: {allowed} | Remaining: {rem}")
        
    # Send the 6th request immediately, which should fail
    allowed, rem = await rate_limiter.check_rate_limit(ident, limit, window)
    logger.info(f"[Request 6 (Burst)] Allowed: {allowed} | Remaining: {rem} (EXPECTED FALSE)")
    
    # Wait for half the window
    logger.info("Waiting 6 seconds...")
    await asyncio.sleep(6)
    
    # Should still fail or succeed depending on original timings? 
    # Since we mocked it and 6s hasn't cleared the 10s window
    allowed, rem = await rate_limiter.check_rate_limit(ident, limit, window)
    logger.info(f"[Request 7 (After 6s)] Allowed: {allowed} | Remaining: {rem} (EXPECTED FALSE since window is 10s)")
    
    # Wait remaining window
    logger.info("Waiting 5 more seconds to clear the sliding window...")
    await asyncio.sleep(5)
    
    # Should succeed now
    allowed, rem = await rate_limiter.check_rate_limit(ident, limit, window)
    logger.info(f"[Request 8 (After total 11s)] Allowed: {allowed} | Remaining: {rem} (EXPECTED TRUE)")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_test())
