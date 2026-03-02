
import asyncio
import sys
import os
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from api.services.db_service import engine
from api.models import Base, User
from api.utils.security import get_password_hash
from api.services.db_service import AsyncSessionLocal

async def init_and_test():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as db:
        # Create a test user with a hashed password
        test_user = User(
            username="security_tester",
            password_hash=get_password_hash("StrongPass123!"),
            is_active=True
        )
        db.add(test_user)
        
        # Create a legacy user with plain text (to show it detects it)
        legacy_user = User(
            username="legacy_tester",
            password_hash="PlainPassword123",
            is_active=True
        )
        db.add(legacy_user)
        
        await db.commit()
    print("✅ Database initialized with 1 Hashed and 1 Plain-text user.")

if __name__ == "__main__":
    asyncio.run(init_and_test())
