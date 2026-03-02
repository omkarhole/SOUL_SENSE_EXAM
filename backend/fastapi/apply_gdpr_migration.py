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
        print("Creating gdpr_scrub_logs table...")
        
        # Check if table exists
        try:
            # PostgreSQL/SQLite portable check via raw SQL
            # For SQLite
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS gdpr_scrub_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username VARCHAR NOT NULL,
                    scrub_id VARCHAR UNIQUE NOT NULL,
                    status VARCHAR DEFAULT 'PENDING',
                    storage_deleted BOOLEAN DEFAULT FALSE,
                    vector_deleted BOOLEAN DEFAULT FALSE,
                    sql_deleted BOOLEAN DEFAULT FALSE,
                    assets_to_delete JSON,
                    retry_count INTEGER DEFAULT 0,
                    last_error TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("Successfully created or verified gdpr_scrub_logs table.")
            # Add indexes
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_gdpr_scrub_logs_user_id ON gdpr_scrub_logs (user_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_gdpr_scrub_logs_scrub_id ON gdpr_scrub_logs (scrub_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_gdpr_scrub_logs_status ON gdpr_scrub_logs (status)"))
        except Exception as e:
            print(f"Migration Error: {e}")

    await engine.dispose()
    print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
