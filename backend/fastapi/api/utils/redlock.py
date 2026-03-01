import uuid
import logging
from typing import Optional, Tuple
from ..services.cache_service import cache_service

logger = logging.getLogger("api.utils.redlock")

# Lua: atomically release ONLY if caller holds the exact lock token (TOCTOU-safe)
_RELEASE_LUA = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""

# Lua: atomically renew TTL ONLY if caller holds the exact lock token (watchdog/heartbeat)
_RENEW_LUA = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("expire", KEYS[1], ARGV[2])
else
    return 0
end
"""


class RedlockService:
    """
    Single-instance Redis locking with Fencing Tokens for Team Vision Documents (#1178).

    IMPORTANT — Locking model clarification:
    This uses a single Redis node with atomic SET NX EX + Lua-guarded release/renew.
    This is NOT a multi-node quorum Redlock (as defined in the antirez Redlock paper).
    The design is intentionally pragmatic for this use-case:
        - Single-node Redis provides mutual exclusion under normal conditions.
        - Fencing Tokens (document version column) act as the final safety net:
          even if a lock TTL races or Redis restarts, stale writes are rejected
          at the database level via the version check.
    """

    def __init__(self):
        self._lock_prefix = "lock:team_vision:"

    def _key(self, resource_id: str) -> str:
        return f"{self._lock_prefix}{resource_id}"

    async def acquire_lock(
        self, resource_id: str, user_id: int, ttl_seconds: int = 30
    ) -> Tuple[bool, Optional[str]]:
        """
        Acquires an exclusive lease on a resource.
        Returns (success, lock_value).

        lock_value format: "<user_id>:<uuid4>"
        The client MUST store this token and present it exactly on every
        PUT update and /renew call to prove they still hold the lease.
        """
        await cache_service.connect()
        lock_key = self._key(resource_id)
        lock_value = f"{user_id}:{uuid.uuid4()}"

        # NX = only set if key doesn't exist (mutual exclusion)
        # EX = auto-expire after TTL so ghost locks cannot persist indefinitely
        success = await cache_service.redis.set(
            lock_key, lock_value, nx=True, ex=ttl_seconds
        )

        if success:
            logger.info(f"[Lock] ACQUIRED resource={resource_id} user={user_id} ttl={ttl_seconds}s")
            return True, lock_value

        # Idempotency: if the same user already holds the lock, renew it
        current_val = await cache_service.redis.get(lock_key)
        if current_val and current_val.startswith(f"{user_id}:"):
            await cache_service.redis.expire(lock_key, ttl_seconds)
            logger.info(f"[Lock] RENEWED (idempotent re-acquire) resource={resource_id} user={user_id}")
            return True, current_val

        logger.warning(
            f"[Lock] DENIED resource={resource_id} user={user_id} — held by {current_val}"
        )
        return False, None

    async def release_lock(self, resource_id: str, lock_value: str) -> bool:
        """
        Releases the lease ONLY if the presented lock_value matches the stored token.
        Uses a Lua script for atomic compare-and-delete (TOCTOU-safe).
        Returns True on success, False if token mismatch or lock already expired.
        """
        await cache_service.connect()
        result = await cache_service.redis.eval(
            _RELEASE_LUA, 1, self._key(resource_id), lock_value
        )
        if result == 1:
            logger.info(f"[Lock] RELEASED resource={resource_id}")
            return True
        logger.warning(
            f"[Lock] Release FAILED resource={resource_id} — invalid token or expired"
        )
        return False

    async def renew_lock(
        self, resource_id: str, lock_value: str, extend_by_seconds: int = 30
    ) -> bool:
        """
        Watchdog / Heartbeat: Extends the TTL of an active lease if the
        caller presents the correct lock_value token.

        Client contract:
          - Call this endpoint every ~20s when the default TTL is 30s.
          - If this returns False, the lock has expired — re-acquire before continuing.

        Uses a Lua script for atomic compare-then-expire (TOCTOU-safe).
        Returns True on success, False if token mismatch or lock already expired.
        """
        await cache_service.connect()
        result = await cache_service.redis.eval(
            _RENEW_LUA, 1, self._key(resource_id), lock_value, str(extend_by_seconds)
        )
        if result == 1:
            logger.info(f"[Lock] RENEWED resource={resource_id} +{extend_by_seconds}s")
            return True
        logger.warning(
            f"[Lock] Renew FAILED resource={resource_id} — invalid token or expired"
        )
        return False

    async def get_lock_info(self, resource_id: str) -> Optional[dict]:
        """
        Returns the full lock metadata for a resource, including the exact
        lock_value token (used for equality check in the update endpoint).
        Returns None if the resource is currently unlocked.
        """
        await cache_service.connect()
        val = await cache_service.redis.get(self._key(resource_id))
        if not val:
            return None

        user_id_str, _ = val.split(":", 1)
        ttl = await cache_service.redis.ttl(self._key(resource_id))

        return {
            "user_id": int(user_id_str),
            "lock_value": val,        # Full token — required for exact equality in PUT
            "expires_in": ttl
        }


redlock_service = RedlockService()
