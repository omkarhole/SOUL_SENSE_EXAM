import asyncio
import os
import sys
import time

# Set PYTHONPATH
test_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(test_dir, "backend", "fastapi")
sys.path.insert(0, project_root)

async def demo_circuit_breaker():
    from api.services.circuit_breaker import CircuitBreaker, CircuitState

    # 1. Mock Redis for the demonstration
    class MockRedis:
        def __init__(self):
            self.store = {}
        async def get(self, key): return self.store.get(key)
        async def set(self, key, val): self.store[key] = val
        async def incr(self, key):
            self.store[key] = int(self.store.get(key, 0)) + 1
            return self.store[key]
        async def delete(self, key): self.store.pop(key, None)

    redis_mock = MockRedis()
    
    # Create breaker with low threshold for quick demo
    service_name = "KAFKA_SERVICE"
    breaker = CircuitBreaker(service_name, failure_threshold=3, recovery_timeout=5)
    breaker.redis = redis_mock # Inject mock

    async def unreliable_external_call():
        print("  [CALL] Attempting to connect to external service...")
        raise ConnectionError("Service connection timed out!")

    async def healthy_external_call():
        print("  [CALL] Attempting to connect to external service...")
        return "SUCCESS"

    print(f"\n{'='*60}")
    print(f"RESILIENCE DEMO: DISTRIBUTED CIRCUIT BREAKER (#1102)")
    print(f"{'='*60}")
    print(f"Initial State: {await breaker.get_state()}")

    print("\n--- PHASE 1: INDUCING FAILURES ---")
    for i in range(3):
        try:
            print(f"Request {i+1}:")
            await breaker.call(unreliable_external_call)
        except Exception as e:
            print(f"  [ERROR] {e}")
            print(f"  [STATE] {await breaker.get_state()}")

    print("\n--- PHASE 2: BREAKER IS OPEN (ZERO-LATENCY FAIL-FAST) ---")
    print("Next request should fail IMMEDIATELY without even attempting the call.")
    start_time = time.time()
    try:
        await breaker.call(unreliable_external_call)
    except Exception as e:
        duration = time.time() - start_time
        print(f"Request 4 (Blocked): {e}")
        print(f"  [METRIC] Execution Time: {duration*1000:.4f}ms (Cascading failure prevented!)")

    print("\n--- PHASE 3: WAITING FOR RECOVERY TIMEOUT (5s) ---")
    await asyncio.sleep(6)
    print(f"State after timeout: {await breaker.get_state()} (Transitioned to HALF_OPEN)")

    print("\n--- PHASE 4: RECOVERY (TRIAL SUCCESS) ---")
    print("Attempting a call while HALF_OPEN...")
    result = await breaker.call(healthy_external_call)
    print(f"  [RESULT] {result}")
    print(f"  [FINAL STATE] {await breaker.get_state()} (Circuit Closed - System Stable)")

if __name__ == "__main__":
    asyncio.run(demo_circuit_breaker())
