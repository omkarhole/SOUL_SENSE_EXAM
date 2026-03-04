from fastapi import APIRouter, Query, Request, Depends, HTTPException
from typing import List, Optional, Dict, Any
from ..services.es_service import get_es_service
from ..routers.auth import get_current_user
from ..models import User
from ..services.semantic_search_service import semantic_search_service
from ..services.db_service import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/search", tags=["Full-Text Search"])

@router.get("/")
async def perform_search(
    q: str = Query(..., min_length=2, description="Search terms"),
    page: int = Query(1, ge=1),
    size: int = Query(10, le=50),
    current_user: User = Depends(get_current_user)
):
    """
    Rich full-text search across journal entries and assessments.
    Supports synonyms (e.g., 'joyful' finds 'happy'), fuzziness, and highlighting.
    """
    es = get_es_service()
    
    tenant_id = getattr(current_user, 'tenant_id', None)
    user_id = current_user.id
    
    # Execute ES Search
    res = await es.search(
        q=q,
        tenant_id=tenant_id,
        user_id=user_id,
        page=page,
        size=size
    )
    
    hits = res.get('hits', {}).get('hits', [])
    total = res.get('hits', {}).get('total', {}).get('value', 0)
    
    results = []
    for hit in hits:
        source = hit.get('_source', {})
        highlight = hit.get('highlight', {}).get('content', [])
        
        results.append({
            "id": source.get('id'),
            "entity": source.get('entity'),
            "score": hit.get('_score'),
            "snippet": highlight[0] if highlight else source.get('content', '')[:150],
            "timestamp": source.get('timestamp')
        })
        
    return {
        "query": q,
        "total": total,
        "page": page,
        "results": results
    }

@router.get("/semantic")
async def semantic_search(
    q: str = Query(..., min_length=2, description="Natural language search query"),
    limit: int = Query(10, le=50),
    min_similarity: float = Query(0.3, ge=0, le=1.0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Semantic search using vector embeddings.
    Finds entries based on emotional context and meaning, even without exact keyword matches.
    """
    results = await semantic_search_service.search_journal_entries(
        db=db,
        query=q,
        user_id=current_user.id,
        limit=limit,
        min_similarity=min_similarity
    )
    
    formatted_results = []
    for r in results:
        # Construct snippets or full entries as needed
        formatted_results.append({
            "id": r["id"],
            "title": r.get("title", ""),
            "snippet": r["content"][:200] + "..." if len(r["content"]) > 200 else r["content"],
            "timestamp": r["timestamp"],
            "similarity": round(r["similarity"], 4),
            "mood_score": r.get("mood_score")
        })
    
    return {
        "query": q,
        "count": len(formatted_results),
        "results": formatted_results,
        "engine": "pgvector"
    }

@router.post("/reindex")
async def trigger_reindex(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Bulk load all existing journal entries into the vector store."""
    # In a real production system, this should check for admin status
    # For now, we'll allow users to reindex their own data or admins to reindex all
    
    is_admin = getattr(current_user, 'is_admin', False)
    user_id = None if is_admin else current_user.id
    
    from ..celery_tasks import reindex_all_entries_task
    task = reindex_all_entries_task.delay(user_id)
    
    return {
        "message": "Reindexing task queued",
        "task_id": task.id,
        "admin_mode": is_admin
    }
