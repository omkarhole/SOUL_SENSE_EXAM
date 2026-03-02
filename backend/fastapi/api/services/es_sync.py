import logging
import asyncio
from typing import Any
from sqlalchemy import event
from sqlalchemy.orm import Session
from .es_service import get_es_service

logger = logging.getLogger(__name__)

async def sync_to_es(entity: str, doc_id: Any, operation: str, data: dict = None):
    """Background task to sync entity state to Elasticsearch."""
    es = get_es_service()
    if operation == "DELETE":
        await es.delete_document(entity, doc_id)
    else:
        await es.index_document(entity, doc_id, data)

def es_sync_listener(mapper, connection, target):
    """SQLAlchemy listener to enqueue ES synchronization."""
    from ..models import JournalEntry, Assessment
    
    # Only sync specific searchable models
    if not isinstance(target, (JournalEntry, Assessment)):
         return

    entity_name = target.__class__.__name__
    doc_id = target.id
    
    # Determine operation based on target state
    from sqlalchemy import inspect
    insp = inspect(target)
    
    if insp.deleted:
        operation = "DELETE"
        data = None
    else:
        operation = "UPDATE" if insp.persistent else "CREATE"
        data = {
            "user_id": target.user_id,
            "tenant_id": getattr(target, 'tenant_id', None),
            # Extract meaningful searchable text
            "content": getattr(target, 'content', '') or getattr(target, 'title', ''),
            "timestamp": getattr(target, 'created_at', None) or getattr(target, 'timestamp', None)
        }

    # Enqueue as a non-blocking background task
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(sync_to_es(entity_name, doc_id, operation, data))
        else:
            # For scripts/management commands where the loop isn't running yet
            asyncio.run(sync_to_es(entity_name, doc_id, operation, data))
    except Exception as e:
        logger.error(f"Failed to trigger ES sync: {e}")

def register_es_listeners():
    """Attach the ES sync logic to SQLAlchemy models."""
    from ..models import JournalEntry, Assessment
    
    for model in [JournalEntry, Assessment]:
        event.listen(model, 'after_insert', es_sync_listener)
        event.listen(model, 'after_update', es_sync_listener)
        event.listen(model, 'after_delete', es_sync_listener)
    
    logger.info("Elasticsearch SQLAlchemy listeners registered.")
