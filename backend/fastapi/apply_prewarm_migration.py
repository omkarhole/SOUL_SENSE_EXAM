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
        print("Adding timezone column to user_settings table...")
        
        try:
            # Add timezone column to user_settings
            await conn.execute(text("ALTER TABLE user_settings ADD COLUMN timezone VARCHAR DEFAULT 'UTC' NOT NULL"))
            print("Successfully added timezone to user_settings table.")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("Column 'timezone' already exists.")
            else:
                print(f"Migration Error: {e}")

    await engine.dispose()
    print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
