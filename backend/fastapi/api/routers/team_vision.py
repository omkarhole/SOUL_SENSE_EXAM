"""API router for Team Vision collaborative document management (#1178)."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated

from ..services.db_service import get_db
from ..models import TeamVisionDocument, User
from .auth import get_current_user
from ..utils.redlock import redlock_service
from ..schemas.team_vision import (
    TeamVisionResponse, TeamVisionCreate, TeamVisionUpdate,
    LockAcquireResponse, LockReleaseRequest,
    LockRenewRequest, LockRenewResponse
)

logger = logging.getLogger("api.routers.team_vision")
router = APIRouter(tags=["Team EI - Vision Documents"])


@router.get("/{document_id}", response_model=TeamVisionResponse)
async def get_team_vision(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_user)] = None
):
    """
    Fetches a Team Vision document.
    Response includes lock_status so the UI can switch to Read-Only mode
    when the document is held by another user.
    """
    stmt = select(TeamVisionDocument).filter(TeamVisionDocument.id == document_id)
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Team Vision Document not found")

    lock_info = await redlock_service.get_lock_info(str(document_id))
    response_dict = doc.to_dict()
    # Expose only user_id + expires_in publicly — do NOT expose lock_value in GET
    response_dict["lock_status"] = (
        {"user_id": lock_info["user_id"], "expires_in": lock_info["expires_in"]}
        if lock_info else None
    )
    return TeamVisionResponse(**response_dict)


@router.post("/{document_id}/lock", response_model=LockAcquireResponse)
async def acquire_vision_lock(
    document_id: int,
    ttl_seconds: int = 30,
    current_user: Annotated[User, Depends(get_current_user)] = None
):
    """
    Acquires an exclusive edit lock using single-instance Redis locking
    (SET NX EX). Returns a `lock_value` token that the client must:
      1. Store locally.
      2. Send with every PUT /update call.
      3. Send with every POST /renew heartbeat call.
      4. Send with the POST /unlock call when done.

    Returns success=False (200) if another user currently holds the lock.
    """
    success, lock_val = await redlock_service.acquire_lock(
        str(document_id), current_user.id, ttl_seconds
    )
    if not success:
        return LockAcquireResponse(
            success=False,
            message="Document is currently locked by another user.",
            expires_in=0
        )
    return LockAcquireResponse(
        success=True,
        lock_value=lock_val,
        message=(
            "Lock acquired. Store lock_value — send it with every PUT update "
            "and POST /renew (heartbeat) call to keep the lease alive."
        ),
        expires_in=ttl_seconds
    )


@router.post("/{document_id}/renew", response_model=LockRenewResponse)
async def renew_vision_lock(
    document_id: int,
    req: LockRenewRequest,
    current_user: Annotated[User, Depends(get_current_user)] = None
):
    """
    Watchdog / Heartbeat endpoint — extends the TTL of an active lock.

    Client contract:
      - Call this every ~20s when the default lock TTL is 30s.
      - If this returns 403, your lock has expired — re-acquire before continuing.

    Validates the exact lock_value token atomically via Lua script before
    extending the TTL (TOCTOU-safe). Returns 403 on token mismatch or expiry.
    """
    success = await redlock_service.renew_lock(
        str(document_id), req.lock_value, req.extend_by_seconds
    )
    if not success:
        raise HTTPException(
            status_code=403,
            detail="Lock renewal failed: invalid token or lock already expired. Re-acquire the lock."
        )
    return LockRenewResponse(
        success=True,
        message=f"Lock extended by {req.extend_by_seconds}s.",
        new_expires_in=req.extend_by_seconds
    )


@router.post("/{document_id}/unlock")
async def release_vision_lock(
    document_id: int,
    req: LockReleaseRequest,
    current_user: Annotated[User, Depends(get_current_user)] = None
):
    """
    Releases the lock using the exact lock_value token.
    Lua-atomic compare-and-delete ensures only the owner can release.
    Returns 403 on token mismatch or if the lock already expired.
    """
    success = await redlock_service.release_lock(str(document_id), req.lock_value)
    if not success:
        raise HTTPException(
            status_code=403,
            detail="Release failed: invalid token or lock already expired."
        )
    return {"message": "Lock released successfully."}


@router.put("/{document_id}", response_model=TeamVisionResponse)
async def update_team_vision(
    document_id: int,
    update_data: TeamVisionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_user)] = None
):
    """
    Saves changes to a Team Vision document.
    Enforces TWO independent safety layers:

    Layer 1 — Exact Lock Token Check:
        update_data.lock_value must match the active Redis lease value exactly.
        This is stricter than a user-id check: it proves the caller holds this
        specific lease instance (not just any lock for that user).

    Layer 2 — Fencing Token (version):
        update_data.version must match doc.version in the database.
        Even if a lock expires and a race occurs, the version mismatch prevents
        any stale write from landing. Returns 409 Conflict on mismatch.
    """
    # --- LAYER 1: Exact lock_value token equality (reviewer gap #2 fix) ---
    lock_info = await redlock_service.get_lock_info(str(document_id))

    if not lock_info:
        raise HTTPException(
            status_code=423,
            detail="No active lock found for this document. Acquire a lock before editing."
        )

    # Exact token equality — not just user_id comparison
    if lock_info["lock_value"] != update_data.lock_value:
        raise HTTPException(
            status_code=403,
            detail=(
                "Lock token mismatch. Your lease may have expired or been "
                "superseded by another session. Re-acquire the lock."
            )
        )

    # Defence-in-depth: embedded user_id in token must also match
    if lock_info["user_id"] != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not own the current lock on this document."
        )

    # --- Fetch record ---
    stmt = select(TeamVisionDocument).filter(TeamVisionDocument.id == document_id)
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # --- LAYER 2: Fencing Token / version check ---
    if doc.version != update_data.version:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Stale update rejected. Server version={doc.version}, "
                f"you sent version={update_data.version}. "
                "Refresh the document and retry."
            )
        )

    # --- Perform update and increment fencing token monotonically ---
    doc.title = update_data.title
    doc.content = update_data.content
    doc.version += 1           # Next writer must present this new value
    doc.last_modified_by_id = current_user.id

    await db.commit()
    await db.refresh(doc)
    return TeamVisionResponse(**doc.to_dict())


@router.post("/", response_model=TeamVisionResponse)
async def create_team_vision(
    data: TeamVisionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Annotated[User, Depends(get_current_user)] = None
):
    """Creates a new Team Vision document."""
    doc = TeamVisionDocument(
        team_id=data.team_id,
        title=data.title,
        content=data.content,
        version=1,
        last_modified_by_id=current_user.id
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return TeamVisionResponse(**doc.to_dict())
