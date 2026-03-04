"""Standardized retry policy helpers for sync and async operations.

Provides a `RetryPolicy` dataclass and lightweight `retry_sync` / `retry_async`
decorators/wrappers that implement exponential backoff with jitter and optional
retry predicates and metrics hooks.

This centralizes retry configuration so services across the app share the same
behavior and observability.
"""
from __future__ import annotations

import asyncio
import time
import random
import logging
from dataclasses import dataclass
from typing import Callable, Any, Optional, Coroutine

logger = logging.getLogger(__name__)


def _default_is_retriable(exc: Exception) -> bool:
    # By default retry on common transient exceptions (network/DB). Services
    # can pass a custom predicate for domain-specific rules.
    from sqlalchemy.exc import OperationalError, DatabaseError, DisconnectionError

    return isinstance(exc, (OperationalError, DatabaseError, DisconnectionError))


@dataclass
class RetryPolicy:
    max_retries: int = 3
    base_delay_ms: float = 100.0
    multiplier: float = 4.0
    jitter_factor: float = 0.1
    is_retriable: Callable[[Exception], bool] = _default_is_retriable
    metrics_callback: Optional[Callable[[str, dict], None]] = None

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay in seconds for given attempt (0-based)."""
        base = self.base_delay_ms * (self.multiplier ** attempt)
        jitter = 1.0 + random.uniform(-self.jitter_factor, self.jitter_factor)
        return (base * jitter) / 1000.0

    def _emit_metric(self, name: str, payload: dict):
        if self.metrics_callback:
            try:
                self.metrics_callback(name, payload)
            except Exception:
                logger.exception("metrics_callback failed")


def retry_sync(policy: RetryPolicy):
    """Decorator for synchronous functions using provided RetryPolicy."""
    def decorator(func: Callable[..., Any]):
        def wrapper(*args, **kwargs):
            for attempt in range(policy.max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 0:
                        policy._emit_metric("retry.success", {"attempts": attempt})
                    return result
                except Exception as e:
                    retriable = policy.is_retriable(e)
                    policy._emit_metric("retry.attempt", {"attempt": attempt, "retriable": retriable})
                    if not retriable:
                        raise
                    if attempt < policy.max_retries:
                        delay = policy.calculate_delay(attempt)
                        logger.warning(f"Transient error, retrying in {delay:.3f}s (attempt {attempt+1})")
                        time.sleep(delay)
                        continue
                    logger.error("Operation failed after retries")
                    raise
        return wrapper
    return decorator


def retry_async(policy: RetryPolicy):
    """Decorator for async functions using provided RetryPolicy."""
    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]):
        async def wrapper(*args, **kwargs):
            for attempt in range(policy.max_retries + 1):
                try:
                    result = await func(*args, **kwargs)
                    if attempt > 0:
                        policy._emit_metric("retry.success", {"attempts": attempt})
                    return result
                except Exception as e:
                    retriable = policy.is_retriable(e)
                    policy._emit_metric("retry.attempt", {"attempt": attempt, "retriable": retriable})
                    if not retriable:
                        raise
                    if attempt < policy.max_retries:
                        delay = policy.calculate_delay(attempt)
                        logger.warning(f"Transient error, retrying in {delay:.3f}s (attempt {attempt+1})")
                        await asyncio.sleep(delay)
                        continue
                    logger.error("Operation failed after retries")
                    raise
        return wrapper
    return decorator


# Convenience default policy for services to import
DEFAULT_POLICY = RetryPolicy()
