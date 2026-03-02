import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add parent directory to path
sys.path.append(os.path.join(os.getcwd(), 'backend', 'fastapi'))

from api.config import get_settings_instance

async def migrate():
    settings = get_settings_instance()
    engine = create_async_engine(settings.async_database_url)
    
    async with engine.begin() as conn:
        print("Adding version column to users table...")
        
        try:
            # Add version column to users
            await conn.execute(text("ALTER TABLE users ADD COLUMN version INTEGER DEFAULT 1 NOT NULL"))
            print("Successfully added version to users table.")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("Column 'version' already exists.")
            else:
                print(f"Migration Error: {e}")

    await engine.dispose()
    print("Migration check complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
