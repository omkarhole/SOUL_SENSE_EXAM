"""
Verify Generation-based Cache Consistency — #1143

Tests:
1. User version increments on update
2. Redis tracks the authoritative version
3. Cache check detects stale version and purges
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.getcwd(), 'backend', 'fastapi'))

from api.services.db_service import AsyncSessionLocal
from api.services.user_service import UserService
from api.services.cache_service import cache_service
from api.models import User
from sqlalchemy import select

async def check_redis_available() -> bool:
    try:
        await cache_service.connect()
        await cache_service.redis.ping()
        return True
    except Exception:
        return False

async def verify_consistency():
    print("--- VERIFYING CACHE CONSISTENCY SAGA ---")
    
    redis_ok = await check_redis_available()
    if not redis_ok:
        print("❌ Redis not available. Skipping consistency test.")
        return

    async with AsyncSessionLocal() as db:
        user_service = UserService(db)
        
        # 1. Setup: Get a user
        stmt = select(User).limit(1)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if not user:
            print("❌ No user found. Run seeding.")
            return
        
        user_id = user.id
        initial_version = user.version or 1
        print(f"Initial Version for user {user.username}: {initial_version}")

        # 2. Test: Populate Cache with current version
        cache_key = f"verify_cache:{user.username}"
        fake_payload = {"id": user_id, "username": user.username, "version": initial_version, "data": "old_data"}
        
        await cache_service.set(cache_key, fake_payload)
        await cache_service.update_version("user", user_id, initial_version)
        print(f"Populated cache with version {initial_version}")

        # 3. Test: Verify cache hit
        data = await cache_service.get_with_version_check(cache_key, "user", user_id)
        assert data is not None and data["version"] == initial_version
        print("✅ Initial cache hit verified.")

        # 4. Test: Update user (triggers version increment)
        print("\nUpdating user to trigger version increment...")
        await user_service.update_user(user_id, username=user.username) # No change, just trigger commit/version logic
        
        # Re-fetch from DB
        await db.refresh(user)
        new_version = user.version
        print(f"New Version in DB: {new_version}")
        assert new_version > initial_version

        # 5. Test: Authoritative version in Redis should be updated
        redis_version = await cache_service.get_latest_version("user", user_id)
        print(f"Authoritative Version in Redis: {redis_version}")
        assert redis_version == new_version

        # 6. Test: Cache hit with STALE data (from a "stale" node perspective)
        # Note: We still have the old fake_payload in the verify_cache key
        # But latest_version is now higher.
        print("\nChecking for consistency catch-up...")
        data = await cache_service.get_with_version_check(cache_key, "user", user_id)
        
        if data is None:
            print("✅ Generation mismatch detected! Cache purged successfully.")
        else:
            print(f"❌ Cache inconsistency! Still returned data for version {data['version']}")

        # 7. Cleanup
        await cache_service.delete(cache_key)
        await cache_service.redis.delete(f"version:user:{user_id}")
        
    print("\n--- CACHE CONSISTENCY VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(verify_consistency())
