import asyncio
import sys
import os
import time

sys.path.append(os.getcwd())

from backend.fastapi.api.services.retry_policy import RetryPolicy, retry_sync, retry_async, DEFAULT_POLICY


def test_calculate_delay_monotonic():
    p = RetryPolicy(base_delay_ms=50, multiplier=2.0, jitter_factor=0)
    d0 = p.calculate_delay(0)
    d1 = p.calculate_delay(1)
    d2 = p.calculate_delay(2)
    assert d0 < d1 < d2


def test_retry_sync_success_after_retry():
    p = RetryPolicy(max_retries=2, base_delay_ms=1, jitter_factor=0, is_retriable=lambda e: True)

    calls = {"n": 0}

    @retry_sync(p)
    def flaky():
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError("transient")
        return "ok"

    start = time.time()
    res = flaky()
    assert res == "ok"
    assert calls["n"] == 2


def test_retry_async_success_after_retry():
    p = RetryPolicy(max_retries=2, base_delay_ms=1, jitter_factor=0, is_retriable=lambda e: True)

    calls = {"n": 0}

    @retry_async(p)
    async def flaky_async():
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError("transient")
        return "ok"

    res = asyncio.run(flaky_async())
    assert res == "ok"
    assert calls["n"] == 2
