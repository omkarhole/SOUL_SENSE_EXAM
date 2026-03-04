import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from api.models import JournalEntry
from api.services.embedding_service import embedding_service
from datetime import datetime

logger = logging.getLogger(__name__)

class SemanticSearchService:
    """Service to handle semantic vector similarity search using pgvector."""

    @staticmethod
    async def search_journal_entries(
        db: AsyncSession,
        query: str,
        user_id: int,
        limit: int = 5,
        min_similarity: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Perform a semantic search for journal entries using cosine similarity.
        """
        # Generate query embedding
        query_vector = await embedding_service.generate_embedding(query)
        if not query_vector:
            return []

        # pgvector uses <=> for cosine distance (1 - cosine similarity)
        # Cosine similarity is calculated as: 1 - (query_vector <=> embedding)
        try:
            # First, check if pgvector extension is available and the column exists
            # In a real app, this should be handled during DB setup
            
            # Using raw SQL for the similarity search as it's the most flexible for pgvector
            # Distance <=> -> Cosine Distance
            # Distance <-> -> Euclidean Distance
            # Distance <#> -> Inner Product
            
            # Convert query_vector list to string format for pgvector, e.g., '[0.1, 0.2, ...]'
            vector_str = "[" + ",".join(map(str, query_vector)) + "]"
            
            stmt = text("""
                SELECT id, title, content, timestamp, mood_score,
                       1 - (embedding <=> :vector) as similarity
                FROM journal_entries
                WHERE user_id = :user_id 
                  AND is_deleted = false
                  AND embedding IS NOT NULL
                  AND (1 - (embedding <=> :vector)) >= :min_similarity
                ORDER BY similarity DESC
                LIMIT :limit
            """)
            
            result = await db.execute(stmt, {
                "vector": vector_str,
                "user_id": user_id,
                "limit": limit,
                "min_similarity": min_similarity
            })
            
            # Mapping result to dict
            rows = result.fetchall()
            search_results = []
            for row in rows:
                search_results.append({
                    "id": row.id,
                    "title": row.title,
                    "content": row.content,
                    "timestamp": row.timestamp,
                    "mood_score": row.mood_score,
                    "similarity": float(row.similarity)
                })
            
            return search_results

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            # Fallback or empty result
            # If the error is about missing operators, it's likely not pgvector-postgres
            if "operator does not exist: vector <=>" in str(e):
                logger.warning("pgvector operators not found, falling back to basic content search.")
                return []
            raise

    @staticmethod
    async def reindex_journal_entries(db: AsyncSession, user_id: Optional[int] = None) -> int:
        """
        Trigger re-indexing of journal entries that don't have embeddings.
        Returns the number of entries queued for indexing.
        """
        # Find entries that need indexing
        stmt = select(JournalEntry.id).where(
            JournalEntry.embedding.is_(None),
            JournalEntry.is_deleted == False
        )
        if user_id:
            stmt = stmt.where(JournalEntry.user_id == user_id)
            
        result = await db.execute(stmt)
        entry_ids = result.scalars().all()
        
        if not entry_ids:
            return 0
            
        from api.celery_tasks import generate_journal_embedding_task
        for entry_id in entry_ids:
            generate_journal_embedding_task.delay(entry_id)
            
        return len(entry_ids)

semantic_search_service = SemanticSearchService()
