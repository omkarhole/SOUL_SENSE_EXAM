
import asyncio
import sys
import os
from pathlib import Path

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy import select
from api.config import get_settings
from api.services.db_service import AsyncSessionLocal
from api.models import User
from api.utils.security import is_hashed

# Force set ENVIRONMENT to development for settings
os.environ["APP_ENV"] = "development"

async def check_passwords():
    settings = get_settings()
    print(f"📡 Database URL: {settings.database_url}")
    print("🔍 Checking database for plain-text passwords...")
    
    async with AsyncSessionLocal() as db:
        stmt = select(User)
        result = await db.execute(stmt)
        users = result.scalars().all()
        
        plain_text_count = 0
        hashed_count = 0
        oauth_count = 0
        
        for user in users:
            if not user.password_hash:
                if user.oauth_sub:
                    oauth_count += 1
                else:
                    print(f"⚠️ User '{user.username}' has NO password hash!")
                    plain_text_count += 1
            elif not is_hashed(user.password_hash):
                print(f"❌ User '{user.username}' has potential PLAIN-TEXT password: {user.password_hash[:3]}***")
                plain_text_count += 1
            else:
                hashed_count += 1
        
        print("\n--- Results ---")
        print(f"✅ Hashed: {hashed_count}")
        print(f"🔒 OAuth: {oauth_count}")
        print(f"❌ Plain-text/Invalid: {plain_text_count}")
        
        if plain_text_count == 0:
            print("\n✨ Database is secure. No plain-text passwords found.")
        else:
            print(f"\n🚨 {plain_text_count} users need password migration at next login.")

if __name__ == "__main__":
    asyncio.run(check_passwords())
