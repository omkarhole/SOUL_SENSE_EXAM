import asyncio
import sys
import os
import pytest

sys.path.append(os.getcwd())

from backend.fastapi.api.services.lock_lease_manager import LeaseRenewalManager, LeaseConfig


@pytest.mark.asyncio
async def test_lease_renewal_stops_on_consecutive_failures():
    calls = {"n": 0}
    lost = {"called": False}

    async def extend_fn(key, token, ttl_ms):
        calls['n'] += 1
        # succeed once then always fail
        return calls['n'] == 1

    def on_lost(key):
        lost['called'] = True

    mgr = LeaseRenewalManager(extend_fn)
    cfg = LeaseConfig(key="k1", token="t1", ttl_ms=1000, renew_interval_seconds=0.05, max_retries=2)

    mgr.start_renewal(cfg, on_lost=on_lost)

    # allow some time for retries
    await asyncio.sleep(0.5)
    # the callback should have been called due to consecutive failures
    assert lost['called'] is True


@pytest.mark.asyncio
async def test_stop_all_cancels_tasks():
    async def extend_fn(key, token, ttl_ms):
        await asyncio.sleep(0.1)
        return True

    mgr = LeaseRenewalManager(extend_fn)
    cfg = LeaseConfig(key="k2", token="t2", ttl_ms=1000, renew_interval_seconds=0.1)
    mgr.start_renewal(cfg)

    # wait briefly then stop all
    await asyncio.sleep(0.2)
    await mgr.stop_all()

    # starting again with same key should be possible
    mgr.start_renewal(cfg)
    await mgr.stop_all()
