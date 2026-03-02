import asyncio
import sys
import os

# Add relevant paths
sys.path.append(os.path.join(os.getcwd(), 'backend', 'fastapi'))

from api.services.db_service import AsyncSessionLocal
from api.models import OutboxEvent, JournalEntry, User
from api.services.journal_service import JournalService
from api.services.encryption_service import current_dek, current_user_id, EncryptionService
from sqlalchemy import select

async def verify_outbox():
    print("--- Verifying Outbox Pattern for Search Indexing ---")
    
    async with AsyncSessionLocal() as db:
        # 1. Setup a test user
        user_stmt = select(User).limit(1)
        user_res = await db.execute(user_stmt)
        user = user_res.scalar_one_or_none()
        
        if not user:
            print("No user found in database. Create one first.")
            return

        # Initialize Encryption Context for the user (#1105)
        dek = await EncryptionService.get_or_create_user_dek(user.id, db)
        current_dek.set(dek)
        current_user_id.set(user.id)
        print(f"Encryption context initialized for user {user.id}")

        journal_service = JournalService(db)
        
        # 2. Clear old indexing outbox events for clean test
        from sqlalchemy import delete
        await db.execute(delete(OutboxEvent).where(OutboxEvent.topic == "search_indexing"))
        await db.commit()
        print("Cleared existing search_indexing outbox events.")

        # 3. Create a journal entry
        print(f"Creating journal entry for user {user.username}...")
        entry = await journal_service.create_entry(
            current_user=user,
            content="Testing exactly-once outbox relay for Elasticsearch synchronization."
        )
        print(f"Journal created: ID {entry.id}")

        # 4. Check outbox
        stmt = select(OutboxEvent).filter(OutboxEvent.topic == "search_indexing", OutboxEvent.status == "pending")
        events = (await db.execute(stmt)).scalars().all()
        
        print(f"Pending outbox events found: {len(events)}")
        for e in events:
            print(f"Event ID: {e.id}, Topic: {e.topic}, Payload: {e.payload}")

        # 5. Simulate update
        print("Updating journal entry...")
        await journal_service.update_entry(entry.id, user, content="Updated content for research.")
        
        events = (await db.execute(select(OutboxEvent).filter(OutboxEvent.topic == "search_indexing", OutboxEvent.status == "pending"))).scalars().all()
        print(f"Pending events after update: {len(events)}")

        # 6. Simulate delete
        print("Deleting journal entry...")
        await journal_service.delete_entry(entry.id, user)
        
        events = (await db.execute(select(OutboxEvent).filter(OutboxEvent.topic == "search_indexing", OutboxEvent.status == "pending"))).scalars().all()
        print(f"Pending events after delete: {len(events)}")

if __name__ == "__main__":
    asyncio.run(verify_outbox())
