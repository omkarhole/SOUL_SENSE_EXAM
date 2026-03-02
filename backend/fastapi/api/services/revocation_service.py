import logging
import asyncio
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, delete
from ..models import TokenRevocation
from ..config import get_settings_instance

logger = logging.getLogger(__name__)

class RevocationService:
    def __init__(self):
        self.settings = get_settings_instance()
        self.bloom_key = "token_revocation_bloom"
        self.redis = None

    async def _get_redis(self):
        if self.redis:
            return self.redis
        try:
            from ..main import app
            self.redis = getattr(app.state, 'redis_client', None)
        except Exception:
            pass
        return self.redis

    async def revoke_token(self, jti: str, expires_at: datetime, db: AsyncSession):
        """Revoke a token by adding it to the Bloom Filter and the database."""
        # 1. Add to SQL (Source of Truth)
        revocation = TokenRevocation(
            token_str=jti, # We reuse the column to store JTI
            expires_at=expires_at,
            revoked_at=datetime.now(timezone.utc)
        )
        db.add(revocation)
        await db.commit()

        # 2. Add to Redis Bloom Filter
        redis = await self._get_redis()
        if redis:
            try:
                # Use standard BF.ADD if RedisBloom is available
                # If not, we fall back to a standard SET for the revocation list
                # (A real bloom filter implementation without the module would use SETBIT)
                await redis.execute_command("BF.ADD", self.bloom_key, jti)
                logger.info(f"Token {jti} added to Redis Bloom Filter")
            except Exception as e:
                # Fallback: Just use a Redis Set if BF module is missing
                logger.warning(f"RedisBloom module not found or failed: {e}. Falling back to Redis Set.")
                await redis.sadd(self.bloom_key + ":set", jti)
                # Set expiration for the whole set if we're not using BF (imperfect but safe)
                await redis.expire(self.bloom_key + ":set", 86400) 

    async def is_revoked(self, jti: str, db: AsyncSession) -> bool:
        """Check if a token is revoked using Bloom Filter with SQL fallback."""
        redis = await self._get_redis()
        
        # 1. Fast path: Bloom Filter check
        if redis:
            try:
                # BF.EXISTS returns 1 if it might exist, 0 if it definitely does not
                exists = await redis.execute_command("BF.EXISTS", self.bloom_key, jti)
                if exists == 0:
                    return False # Definitely not revoked
            except Exception:
                # Fallback check in Redis Set
                if await redis.sismember(self.bloom_key + ":set", jti):
                    pass # Potential revoked, proceed to SQL check
                else:
                    return False

        # 2. Slow path: SQL check (handles False Positives from Bloom Filter)
        stmt = select(TokenRevocation).filter(TokenRevocation.token_str == jti)
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def cleanup_expired_tokens(self, db: AsyncSession):
        """Remove expired tokens from the revocation list."""
        now = datetime.now(timezone.utc)
        stmt = delete(TokenRevocation).where(TokenRevocation.expires_at < now)
        await db.execute(stmt)
        await db.commit()
        # Note: Bloom filters can't easily have individual items removed. 
        # Typically you'd re-create the filter periodically from the SQL DB.

revocation_service = RevocationService()
