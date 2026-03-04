"""Distributed lock lease renewal safety manager.

Provides a small, testable manager that renews distributed lock leases (TTL)
via a provided extend_fn. It ensures renewals are retried with backoff,
stops renewing when ownership is lost, and emits optional metrics/logs.

The manager is agnostic to the locking backend (Redis, etc.) — callers pass
an async `extend_fn(key, token, ttl_ms)` which should perform an atomic
extend only if the token matches (common Redis Lua pattern) and return True
on success.
"""
from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Awaitable

logger = logging.getLogger(__name__)


@dataclass
class LeaseConfig:
    key: str
    token: str
    ttl_ms: int = 10000
    renew_interval_seconds: float = 3.0
    max_retries: int = 5
    jitter_factor: float = 0.1


class LeaseRenewalManager:
    """Manage background renewal tasks for distributed lock leases."""

    def __init__(self, extend_fn: Callable[[str, str, int], Awaitable[bool]], *, metrics_cb: Optional[Callable[[str, dict], None]] = None):
        """Create manager.

        extend_fn: async function (key, token, ttl_ms) -> bool
        metrics_cb: optional callback for emitting metrics: metrics_cb(name, payload)
        """
        self.extend_fn = extend_fn
        self.metrics_cb = metrics_cb
        self._tasks: Dict[str, asyncio.Task] = {}
        self._stop = False

    def _emit(self, name: str, payload: dict):
        if self.metrics_cb:
            try:
                self.metrics_cb(name, payload)
            except Exception:
                logger.exception("metrics_cb failed")

    def start_renewal(self, cfg: LeaseConfig, on_lost: Optional[Callable[[str], None]] = None):
        """Start background renewal for the given lease config.

        Returns a key identifying the renewal (cfg.key).
        """
        if cfg.key in self._tasks:
            raise RuntimeError(f"Renewal already running for {cfg.key}")

        task = asyncio.create_task(self._renew_loop(cfg, on_lost))
        self._tasks[cfg.key] = task
        logger.info(f"Started lease renewal for {cfg.key}")
        return cfg.key

    async def _renew_loop(self, cfg: LeaseConfig, on_lost: Optional[Callable[[str], None]]):
        consecutive_failures = 0
        # initial small jitter to avoid thundering herd
        await asyncio.sleep(random.uniform(0, cfg.renew_interval_seconds * cfg.jitter_factor))

        while not self._stop:
            try:
                success = await self.extend_fn(cfg.key, cfg.token, cfg.ttl_ms)
                self._emit("lease.renew.attempt", {"key": cfg.key, "success": success})
                if success:
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    logger.warning(f"Lease renewal failed for {cfg.key} (attempts={consecutive_failures})")

                if consecutive_failures > cfg.max_retries:
                    logger.error(f"Lease lost for {cfg.key} after {consecutive_failures} failed renewals")
                    self._emit("lease.lost", {"key": cfg.key, "failures": consecutive_failures})
                    if on_lost:
                        try:
                            on_lost(cfg.key)
                        except Exception:
                            logger.exception("on_lost callback failed")
                    break

            except asyncio.CancelledError:
                logger.info(f"Lease renewal cancelled for {cfg.key}")
                break
            except Exception as e:
                consecutive_failures += 1
                logger.exception(f"Error during lease renewal for {cfg.key}: {e}")

            # Backoff with jitter on failure; otherwise sleep regular interval
            if consecutive_failures:
                backoff = min(cfg.renew_interval_seconds * (2 ** (consecutive_failures - 1)), cfg.ttl_ms / 1000.0)
                backoff *= 1.0 + random.uniform(-cfg.jitter_factor, cfg.jitter_factor)
                await asyncio.sleep(backoff)
            else:
                await asyncio.sleep(cfg.renew_interval_seconds)

        # Cleanup task entry
        self._tasks.pop(cfg.key, None)

    async def stop_renewal(self, key: str, timeout: float = 5.0):
        """Stop a specific renewal and wait up to timeout seconds."""
        task = self._tasks.get(key)
        if not task:
            return
        task.cancel()
        try:
            await asyncio.wait_for(task, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout while stopping renewal {key}")
        except asyncio.CancelledError:
            pass

    async def stop_all(self):
        """Stop all renewals and wait for tasks to finish."""
        self._stop = True
        tasks = list(self._tasks.values())
        for t in tasks:
            t.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()
