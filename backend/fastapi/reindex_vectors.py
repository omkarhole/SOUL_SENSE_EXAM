import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Mock environment variables if needed
os.environ.setdefault("APP_ENV", "development")

from api.services.db_service import AsyncSessionLocal
from api.services.semantic_search_service import semantic_search_service
from api.models import JournalEntry
from sqlalchemy import select

async def main():
    print("Starting Semantic Vector Re-indexing...")
    async with AsyncSessionLocal() as db:
        # Get count of entries without embeddings
        stmt = select(JournalEntry.id).where(JournalEntry.embedding.is_(None))
        result = await db.execute(stmt)
        entry_ids = result.scalars().all()
        
        print(f"Found {len(entry_ids)} entries needing indexing.")
        
        if not entry_ids:
            print("Everything up to date.")
            return

        # Trigger indexing via service (which uses Celery)
        # Or we can do it synchronously here for a migration script
        count = await semantic_search_service.reindex_journal_entries(db)
        print(f"Queued {count} entries for background indexing.")
        print("Check Celery worker logs for progress.")

if __name__ == "__main__":
    asyncio.run(main())
