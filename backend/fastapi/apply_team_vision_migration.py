import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add parent directory to path to reach api module
sys.path.append(os.path.join(os.getcwd(), 'backend', 'fastapi'))

from api.config import get_settings_instance

async def migrate():
    settings = get_settings_instance()
    engine = create_async_engine(settings.async_database_url)
    
    async with engine.begin() as conn:
        print("Creating team_vision_documents table...")
        
        # SQL for creating the table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS team_vision_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id VARCHAR(100) NOT NULL,
            title VARCHAR(200) NOT NULL,
            content TEXT NOT NULL,
            version INTEGER DEFAULT 1 NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_modified_by_id INTEGER,
            FOREIGN KEY (last_modified_by_id) REFERENCES users(id)
        );
        """
        await conn.execute(text(create_table_sql))
        
        # Create index
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_team_vision_lookup ON team_vision_documents (team_id, id);"))
        
        print("Successfully created team_vision_documents table and indexes.")

    await engine.dispose()
    print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
