
import asyncio
import time
import requests
import json
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://127.0.0.1:8000"

def make_request(i):
    try:
        start = time.time()
        # AnalyticsEventCreate: anonymous_id, event_type, event_name, event_data
        resp = requests.post(f"{BASE_URL}/api/v1/analytics/events", 
                            json={
                                "anonymous_id": "test-client-123456789",
                                "event_type": "test_burst", 
                                "event_name": f"ping_{i}",
                                "event_data": {"val": i}
                            },
                            headers={"Content-Type": "application/json"})
        end = time.time()
        
        remaining = resp.headers.get("X-RateLimit-Remaining", "N/A")
        return i, resp.status_code, remaining, round(end-start, 3)
    except Exception as e:
        return i, "ERROR", str(e), 0

async def demo_burst():
    print(f"\n{'='*70}")
    print("ADAPTIVE TOKEN-BUCKET RATE LIMITER VERIFICATION (#1111)")
    print(f"{'='*70}")
    print("Scenario: Sending 5 rapid requests to /api/v1/analytics/events")
    print("Expectation: Status 201 and X-RateLimit headers present.")
    print(f"{'='*70}\n")

    with ThreadPoolExecutor(max_workers=5) as executor:
        loop = asyncio.get_event_loop()
        tasks = [loop.run_in_executor(executor, make_request, i) for i in range(5)]
        results = await asyncio.gather(*tasks)

    results.sort()
    for i, status, remaining, duration in results:
        stat_icon = "✅" if status == 201 else "❌" if status == 429 else "⚠️"
        print(f"Request {i+1:02}: Status {status} {stat_icon} | Remaining: {remaining:3} | Latency: {duration}s")

    print(f"\n{'='*70}")
    print("Verification complete.")
    print(f"{'='*70}")

if __name__ == "__main__":
    asyncio.run(demo_burst())
