import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Mock environment variables if needed
os.environ.setdefault("APP_ENV", "development")

from api.services.db_service import AsyncSessionLocal, engine
from api.services.embedding_service import embedding_service
from api.models import JournalEntry, Base
from api.services.encryption_service import current_dek
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Set a dummy DEK for the demo so we can read/write encrypted content
DUMMY_DEK = b'\0' * 32
current_dek.set(DUMMY_DEK)

# Override engine to use in-memory SQLite for a clean demo
demo_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
DemoSession = async_sessionmaker(demo_engine, class_=AsyncSession, expire_on_commit=False)

async def demo_semantic_workflow():
    print("=== SoulSense Semantic Search Terminal Demo ===")
    
    # Init in-memory DB
    async with demo_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 1. Create dummy entries
    async with DemoSession() as db:
        print("Creating dummy entries for demo...")
        dummy_entries = [
            JournalEntry(username="demo", content="I feel really overwhelmed with work and exams, but also hopeful that things will get better soon.", title="Stress and Hope"),
            JournalEntry(username="demo", content="Had a great day at the park. The sun was shining and I felt very relaxed and peaceful.", title="Sun and Peace"),
            JournalEntry(username="demo", content="I'm feeling very sad today. Everything feels dark and heavy.", title="Gray Day")
        ]
        for de in dummy_entries:
            db.add(de)
        await db.commit()
        
        stmt = select(JournalEntry)
        result = await db.execute(stmt)
        entries = result.scalars().all()

        print(f"Entries to index: {len(entries)}")
        
        # 2. Re-indexing Demo (Synchronous for the terminal output)
        print("\n--- Phase 1: Embedding Generation ---")
        for entry in entries:
            print(f"Indexing entry #{entry.id}: '{entry.content[:40]}...'")
            try:
                # Combine title and content if title exists
                text_to_embed = f"{entry.title}: {entry.content}" if entry.title else entry.content
                embedding = await embedding_service.generate_embedding(text_to_embed)
                
                if embedding:
                    entry.embedding = embedding
                    entry.embedding_model = embedding_service.model_name
                    print(f"  [OK] Generated {len(embedding)}-dim vector using {embedding_service.model_name}")
                else:
                    print(f"  [FAILED] No vector generated")
            except Exception as e:
                print(f"  [ERROR] {e}")
                print("  (Note: If this fails, make sure 'sentence-transformers' is installed: pip install sentence-transformers)")
                return

        await db.commit()
        print("--- All embeddings stored in database ---")

        # 3. Search Demo
        print("\n--- Phase 2: Semantic Search Simulation ---")
        queries = [
            "I'm feeling anxious about my performance",
            "happiness and nature",
            "darkness and sadness"
        ]

        for q in queries:
            print(f"\nUser Query: '{q}'")
            query_vector = await embedding_service.generate_embedding(q)
            
            # Since SQLite doesn't have <=> operator, we'll do similarity in Python for this demo
            # But in the real app on Postgres, the db handles this.
            
            from scipy.spatial.distance import cosine
            
            similarities = []
            for entry in entries:
                if entry.embedding:
                    # cosine distance = 1 - similarity. We want similarity = 1 - distance
                    # but cosine function from scipy returns distance.
                    # sim = 1 - cosine(v1, v2)
                    # For simplicity, if scipy is not here, we'll mock or use a simple dot product
                    try:
                        import numpy as np
                        sim = 1 - cosine(query_vector, entry.embedding)
                    except:
                        # Fallback simple dot product
                        v1 = np.array(query_vector)
                        v2 = np.array(entry.embedding)
                        sim = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                    
                    similarities.append((entry, sim))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            for entry, sim in similarities[:2]:
                print(f"  => Match: [Sim {sim:.4f}] Entry #{entry.id}: '{entry.content[:60]}...'")

if __name__ == "__main__":
    try:
        asyncio.run(demo_semantic_workflow())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Demo failed: {e}")
